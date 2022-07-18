from threading import Thread, Lock
from datetime import datetime
# from psutil import *
import subprocess
import ReadEXCEL
import MyTestPlan
import GlobalVariables
import GlobalFunctions
import time
import os

# Lock
file_lock = Lock()

start_t = None


class MyThread(Thread):
    def __init__(self, thread_id, port, reproduce_run, dic_cmd=None):
        Thread.__init__(self)
        self.thread_id = thread_id
        self.port = port
        self.reproduce_run = reproduce_run
        self.process = -100
        self.dic_cmd = dic_cmd

    def print_data(self):
        GlobalVariables.logger.info("\nthread id: " + str(self.thread_id))
        GlobalVariables.logger.info("\ndevice name: " + str(self.port.device_name))

    def run(self):
        """
        Start to run current thread instance/
        """
        try:
            # the thread was created for reproduce run
            if self.reproduce_run is True:
                GlobalVariables.running_threads_dic[self.thread_id] = self

                GlobalVariables.logger.info("\nHi to " + self.thread_id)

                self.start_reproduce_thread_run(self.dic_cmd)

                GlobalVariables.logger.info("\ni finished my run " + self.port.device_name + " " + self.thread_id)
                del GlobalVariables.running_threads_dic[self.thread_id]

                GlobalVariables.status_device_reproduce_lock.acquire()
                GlobalVariables.status_devices_to_reproduce[self.dic_cmd["device_name"]] = True
                GlobalVariables.status_device_reproduce_lock.release()

            # the thread was created for regular run
            else:
                if GlobalVariables.tests_queue.is_empty() is False:
                    GlobalVariables.second_threads_lock.acquire()
                    GlobalVariables.running_threads_dic[self.thread_id] = self
                    GlobalVariables.second_threads_lock.release()
                    GlobalVariables.tests_lock.acquire()
                    test = GlobalVariables.tests_queue.dequeue()
                    GlobalVariables.tests_lock.release()

                    self.start_thread_run(test)

                    # TODO if the last test isnt like last thread with some giga? we make the running longer!!

                    del GlobalVariables.running_threads_dic[self.thread_id]
                    GlobalVariables.logger.info("del Thread")
                    # TODO stop the event? https://stackoverflow.com/questions/323972/ is-there-any-way-to-kill-a-thread-in-python

                    # if num of remainder tests is bigger then available threads, create new thread
                    GlobalVariables.first_threads_lock.acquire()
                    if GlobalVariables.tests_queue.size() > GlobalVariables.threads_queue.size():
                        GlobalVariables.threads_queue.enqueue(MyThread(self.thread_id, self.port,
                                                                       reproduce_run=False))
                    GlobalVariables.first_threads_lock.release()

                else:
                    GlobalVariables.logger.info("Empty queue. \n thread " + str(self.thread_id) + " is inactive....")

        except Exception as e:
            GlobalVariables.logger.error(e.message)

    def start_thread_run(self, test):
        """
        This function got a test and start to run it.
        if the test need to run on Magic port the test will be
        pushed again into the queue.

        :param test: instance of MyTestPlan class
        """
        try:
            if test.giga_for_test == self.port.giga:
                self.print_data()

                test.cmd = self.fill_port_details_in_cmd(test, self.port)

                if ('Client' in test.name or 'client' in test.name) and 'IEEE1588' not in test.name:
                    test.server_cmd = self.fill_port_details_in_server_cmd(test, self.port)
                    self.save_server_cmd_in_file(test.log_dir, test.server_cmd)

                test.print_data()

                self.run_and_check(test)

            else:
                GlobalVariables.tests_queue.enqueue(test)

        except Exception as e:
            GlobalVariables.logger.error(e.message)

    def start_reproduce_thread_run(self, dic):
        """
        *** FOR REPRODUCE OF FAILURES ONLY ***

        This function got a dictionary with details of failures to reproduce, and reproduce them.

        :param dic: cmd": cmd_to_run, "device_name": device_name, "protocol": protocol, "name": name test

        """
        test = MyTestPlan.MyTestPlan(dic["protocol"], dic["name"], None,
                                     is_server_needed_client=False, is_reproduce=True, log_dir=dic["new_path"])
        test.cmd = dic["cmd"]
        GlobalVariables.logger.info(test.protocol + " " + test.name + " " + test.cmd)

        if ('Client' in dic["name"] or 'client' in dic["name"]) and 'IEEE1588' not in dic["name"]:
            my_file = open(dic["old_path"] + "/server_cmd.txt", 'r')
            server_cmd = my_file.readline()
            my_file.close()

            # update server CMD
            test.server_cmd = server_cmd
            test.testplan_line = test.server_cmd[:test.server_cmd.find('.testplan')]
            test.is_server_needed_client = True

        # run client/regular
        self.run_and_check(test)

    def fill_port_details_in_cmd(self, test, port):
        """
        This function fill the CMD of a given test with the missing details of the port that will run it.
        :param test: test to update his CMD with ports details
        :param port: port that will run the given test

        :return: the full CMD- with the port details

        """
        full_cmd = test.cmd.format(ip=port.ip, mac=port.mac, virtual_ip=port.virtual_ip, virtual_mac=port.virtual_mac,
                                   device_name=port.device_name, ipv6=port.ipv6, log_dir=test.log_dir)
        return full_cmd

    def fill_port_details_in_server_cmd(self, test, port):
        """
        This function fill the CMD of a given server test with the missing details of the port that will run it.
        :param test: server test to update his CMD with ports details
        :param port: port that will run the given server test

        :return: the full CMD - with the port details
        """
        full_cmd = test.server_cmd.format(ip=port.virtual_ip, mac=port.virtual_mac, virtual_ip=port.ip,
                                          virtual_mac=port.mac, ipv6=port.ipv6_LP, device_name=port.device_name)
        # , log_dir=test.server_log_dir)
        return full_cmd

    def update_test_run_time(self, str_part_of_run, test):
        """
        This function update part of run time in the file of specific test run.
        """
        path = test.log_dir + '/RunTime.txt'
        f = open(path, 'r+')

        list_lines = f.readlines()
        GlobalVariables.logger.info("path = " + path)

        if 'start' in str_part_of_run:
            f.write('start=' + str(datetime.now()) + '\n')
            f.close()
            ReadEXCEL.update_test_status_in_excel(GlobalVariables.path_to_XL, test.name, "RUNNING", "--:--:--", test.log_dir)

        elif 'running' in str_part_of_run:
            # if len(list_lines) == 2:
            #     # delete the line of running time
            #     subprocess.call(['sed', '-i', '/.*' + 'running' + ',.*/d', path])
            #     GlobalVariables.logger.info('big from 2 - ' + str(len(list_lines)))
            # else:
            #     GlobalVariables.logger.info('less from 2 - ' + str(len(list_lines)))
            start = list_lines[0]
            start = start[(start.find('=') + 1):start.find('\n')]
            GlobalVariables.logger.info("old start: '" + start + "'")

            date_time_obj = datetime.strptime(start, '%Y-%m-%d %H:%M:%S.%f')
            current_time = GlobalFunctions.get_time(date_time_obj)
            seconds = current_time.total_seconds()
            f.write('seconds-' + str(seconds) + '|running=' + str(current_time) + '\n')
            f.close()

            GlobalVariables.logger.info('running=' + str(current_time) + '\n')
            # TODO need it? it will take much more time... (check all the XL results file for every update of XL...)
            # ReadEXCEL.update_test_status_in_excel(GlobalVariables.path_to_XL, test.name, "RUNNING", current_time, test.log_dir)

    def subprocess_run(self, cmd):
        """
        run cmd of Defensics test
        :param test: the obj test to run
        """
        self.process = subprocess.call(cmd, shell=True)
        time.sleep(5)

    def background_print(self, test):
        """
        print for every test that run every part of time the status of the full run
        """
        # while the current test doesn't finish
        while self.process == -100:
            time.sleep(10)

            # print all status of run: run time, ping, number of finished/running tests
            GlobalFunctions.print_status_of_run()

            # update private RunTime.txt of run with current run time when it's *RUNNING*
            self.update_test_run_time('running', test)

            # if we are in reproducing of failure it take much less time
            #  than a regular run there fore w'll wait less time.
            if self.reproduce_run is False:
                time.sleep(300)
            else:
                time.sleep(30)

    def start_run_defensics(self, test):
        """
        This function start 2 threads in parallel:
            1) cmd of failures reproducing
            2) ping to device in order to check aliveness

        :param cmd: command to reproduce failures
        """
        # update private RunTime.txt of run that this run had *START*
        self.update_test_run_time('start', test)

        # create first thread that will run the test
        thread = Thread(target=self.subprocess_run, args=(test.cmd,), name='cmd test')

        # TODO - deamon needed??
        # thread.daemon = True

        # create second thread that will run in background and print status of run
        thread2 = Thread(target=self.background_print, args=(test,), name='ping test')
        # start the threads
        thread.start()
        thread2.start()
        # wait to the threads to finish
        thread.join()
        thread2.join()

    def run_and_check(self, test):
        """
        Function that run cmd and check results.
        also update status and files

        :param test: test to run
        """
        global start_t
        start_t = datetime.now()

        path_to_finished_runs_file = GlobalVariables.path_to_lists_runs_details + '/ListOfFinishedRunsDetails.txt'
        path_to_running_runs_file = GlobalVariables.path_to_lists_runs_details + '/ListOfRunningRunsDetails.txt'
        path_to_waiting_runs_file = GlobalVariables.path_to_lists_runs_details + '/ListOfWaitingRunsDetails.txt'
        global_path = GlobalVariables.path_to_lists_runs_details + '/' + test.protocol + '/' + test.name
        path_to_results = (global_path + '/run-time-info.xml')

        # delete the line of run from the file that collect all WAITING runs
        subprocess.call(['sed', '-i', '/,' + test.name + ',/d', path_to_waiting_runs_file])

        time.sleep(30)

        # run Defensics CMD
        process = self.call_defensics_to_run(test)

        # check big timer
        time_run = GlobalFunctions.get_time_from_file(global_path)
        time_run_2 = GlobalFunctions.get_time(start_t)

        if time_run is None or time_run == '--:--:--' or time_run == '':
            time_run = time_run_2
        else:
            seconds = GlobalFunctions.get_time_from_file(global_path, is_for_seconds=1)
            seconds_2 = time_run_2.total_seconds()
            if float(seconds) < seconds_2:
                time_run = time_run_2

        GlobalVariables.logger.info("Run time: " + str(time_run))

        # cover all the optional results of runs
        if process == 0:
            GlobalVariables.logger.info(
                "test: " + test.name + " finished successfully - pass!! :) [on port " + self.port.device_name + "]")
            GlobalVariables.logger.info("The test run executed with no failures")
            ReadEXCEL.update_test_status_in_excel(GlobalVariables.path_to_XL, test.name, "finished!! - PASS",
                                                 time_run, test.log_dir)
            succeeded = 0
        elif process == 1:
            GlobalVariables.logger.error(
                "test: " + test.name + " didn't succeeded - error!! :( [on port " + self.port.device_name + "]")
            GlobalVariables.logger.error("The test run did not complete due to error, or no cases executed")
            ReadEXCEL.update_test_status_in_excel(GlobalVariables.path_to_XL, test.name,
                                                  "ERROR- The test run did not complete due to error or no cases executed",
                                                  time_run, test.log_dir)
            succeeded = 0
        elif process == 2:
            GlobalVariables.logger.warning(
                "test: " + test.name + " didn't succeeded - fail!! :( [on port " + self.port.device_name + "]")
            GlobalVariables.logger.warning("The test run executed with inconclusive or failed cases")
            ReadEXCEL.update_test_status_in_excel(GlobalVariables.path_to_XL, test.name, "finished!! - FAIL",
                                                  time_run, test.log_dir)
            succeeded = 0
        elif process == 3:
            GlobalVariables.logger.error(
                "test: " + test.name + " didn't succeeded!! :( [on port " + self.port.device_name + "]")
            GlobalVariables.logger.error("Trying to resume an already finished test run")
            ReadEXCEL.update_test_status_in_excel(GlobalVariables.path_to_XL, test.name,
                                                  "ERROR- Trying to resume an already resume test run", time_run,
                                                  test.log_dir)
            succeeded = 1
        elif process == 4:
            GlobalVariables.logger.critical(
                "test: " + test.name + " didn't succeeded - no license!! :( [on port " + self.port.device_name + "]")
            GlobalVariables.logger.critical("No license for suite")
            ReadEXCEL.update_test_status_in_excel(GlobalVariables.path_to_XL, test.name,
                                                  "ERROR- No license for suite", time_run, test.log_dir)
            succeeded = 1
        elif process == 5:
            GlobalVariables.logger.critical(
                "test: " + test.name + " didn't succeeded!! :( [on port " + self.port.device_name + "]")
            GlobalVariables.logger.critical("Instrumentation maximum count or time limit exceeded")
            ReadEXCEL.update_test_status_in_excel(GlobalVariables.path_to_XL, test.name,
                                                  "ERROR- Instrumentation maximum count or time limit exceeded",
                                                  time_run, test.log_dir)
            succeeded = 1
        elif process == 6:
            GlobalVariables.logger.warning(
                "test: " + test.name + " didn't succeeded!! :( [on port " + self.port.device_name + "]")
            GlobalVariables.logger.warning("Warnings (for SafeGuard feature)")
            ReadEXCEL.update_test_status_in_excel(GlobalVariables.path_to_XL, test.name,
                                                  "finished!! - WARNING (for SafeGuard feature)", time_run,
                                                  test.log_dir)
            succeeded = 0

        elif process == -1:
            succeeded = -1

        else:
            GlobalVariables.logger.warning(
                "test: " + test.name + " didn't succeeded!! :( [on port " + self.port.device_name + "]")
            GlobalVariables.logger.warning("Unknown reason")
            ReadEXCEL.update_test_status_in_excel(GlobalVariables.path_to_XL, test.name,
                                                  "ERROR- failed due to UNKNOWN REASON", time_run, test.log_dir)
            succeeded = 0

        # delete the line of run from the file that collect all RUNNING runs
        subprocess.call(['sed', '-i', '/.*,' + test.name + ',.*/d', path_to_running_runs_file])

        # in case test didn't ran properly, don't check the run results
        if succeeded != 0 or not os.path.exists(path_to_results):
            GlobalVariables.logger.error("test FAILED!!")
            full_status = ReadEXCEL.read_status_test(GlobalVariables.path_to_XL, test.name)
            new_line_about_run = ("\ntest failed during run!! " + full_status + ',' + test.name + ',' + test.protocol + ',' +
                                  str(GlobalVariables.date) + ',' + str(time_run))

        # in case test ran properly,save the run results directory
        else:
            new_line_about_run = ('\n' + path_to_results + ',' + test.name + ',' + test.protocol +
                                  ',' + str(GlobalVariables.date) + ',' + str(time_run))

        GlobalVariables.num_finished_tests += 1
        GlobalVariables.num_running_tests -= 1

        try:
            # add the result into the file that collect all runs results
            self.add_to_runs_file(path_to_finished_runs_file, new_line_about_run)

        except Exception as e:
            GlobalVariables.logger.error('ERROR occured during running test ' + test.name + '.\n Error: ' + e.message)

    def process_1_server(self, base_test):
        """
         This function run the cmd of the Server in remote on DUT side, in order to start Client run on LP side

        :param base_test: basic test that should be run- .
        :return:
        """
        test_name = base_test.name.replace('Client', 'Server')

        with open(GlobalVariables.path_to_save_server_log, 'w+') as my_file:
            try:
                my_file.write("IN REMOTE PROCESS - SERVER SIDE\n")
                my_file.write(test_name + '\n')
                my_file.write("server_cmd: " + base_test.server_cmd)

                GlobalVariables.ssh_lock.acquire()
                GlobalVariables.logger.info("running ssh {} '{}'".format(GlobalVariables.DUT_machine, base_test.server_cmd))
                remote_proccess = subprocess.Popen("ssh {} '{}'".format(GlobalVariables.DUT_machine, base_test.server_cmd),
                                                   stdout=my_file, shell=True, stderr=subprocess.PIPE)
                time.sleep(5)
                GlobalVariables.ssh_lock.release()

                GlobalVariables.logger.info("waiting 5 ms........")
                time.sleep(5)

                # process_work = subprocess.call(('ssh {}  "pid=\$(ps -aux | grep \'java\' | grep \'{}\' | grep \'{}\' '
                #                                 '| tr -s \' \' | cut -d \' \' -f 2); echo \$pid"').format
                #                                (GlobalVariables.DUT_machine, base_test.testplan_line, self.port.ip),
                #                                shell=True, stderr=subprocess.PIPE)
                # GlobalVariables.logger.info("--------------------" + str(process_work))
                my_file.write("remote_proccess for test: " + test_name + " is " + str(remote_proccess))
                return remote_proccess

            except Exception as e:
                my_file.write('ERROR occured during running test ' + test_name + '.\n Error: ' + e.message)
                GlobalVariables.logger.error("error occurred")
            return "ERROR"

    def call_defensics_to_run(self, test):
        """
        Starting to run Defensics CMD and then check possible responses

        :param test: test to run
        :return: 0 - in case run finished successfully
                 1 - in case run finished with error
        """
        try:
            proc_server_client = 0

            # do remote command before run
            if test.is_server_needed_client is True:
                GlobalFunctions.create_logger("server_output.log")

                proc_server_client = self.process_1_server(test)

            # add the new run into the file that collect all running runs status
            path_to_results = GlobalVariables.path_to_lists_runs_details + '/' \
                              + test.protocol + '/' + test.name + '/run-time-info.xml'
            path_to_running_runs_file = GlobalVariables.path_to_lists_runs_details + '/ListOfRunningRunsDetails.txt'
            new_line_about_run = '\n' + path_to_results + ',' + test.name + ',' + test.protocol + \
                                 ',' + str(GlobalVariables.date) + ',stuck'
            file_lock.acquire()
            self.add_to_runs_file(path_to_running_runs_file, new_line_about_run)
            file_lock.release()

            # TODO uncoment
            GlobalVariables.logger.info("starting test: " + test.name + " on port " + str(self.port.device_name))
            GlobalVariables.num_running_tests += 1

            # starting to run the process of Defensics
            self.start_run_defensics(test)

            process = self.process
            GlobalVariables.logger.info("my process: " + str(process))
            # no need now.... time_run = GlobalFunctions.get_time(start_t)

            if test.is_server_needed_client is True:
                GlobalVariables.logger.info("*server run* will be killed.....")

                kill_line = 'ssh {}  "pid=\$(ps -aux | grep java | grep testplan | tr -s \' \' | cut -d \' \' -f 2 ); ' \
                            'echo \$pid | xargs kill -9"'
                #kill_line = 'ssh {}  "pid=\$(ps -aux | grep \'tcpreplay\' | grep \'{}\' ' \
                #           '| tr -s \' \' | cut -d \' \' -f 2); echo \$pid | xargs kill"'
                kill_process = subprocess.call(kill_line.format
                                               (GlobalVariables.DUT_machine, self.port.device_name),
                                               shell=True, stderr=subprocess.PIPE)
                # TODO remove
                GlobalVariables.logger.info(kill_line.format(GlobalVariables.DUT_machine, self.port.device_name))
                GlobalVariables.logger.info("*remote process* will be killed.....")
                proc_server_client.kill()
                GlobalVariables.logger.info("server and remote process where killed")

            return process

        except Exception as e:
            GlobalVariables.logger.error('ERROR occured during running test ' + test.name + '.\n Error: ' + e.message)
            GlobalVariables.logger.error("Stopped test: " + test.name + " [of port " + self.port.device_name + "] - because of error")
            ReadEXCEL.update_test_status_in_excel(GlobalVariables.path_to_XL, test.name,
                                                  "ERROR occured during running", "--:--:--", test.log_dir)
            return -1

    def add_to_runs_file(self, path_to_file, new_line_about_run):
        """
        This function add a line about run in specific file

        :param path_to_file: file to update with new line about run
        :param new_line_about_run: details of specific run in a line
        """
        results_file = open(path_to_file, 'a')
        results_file.write(new_line_about_run)
        results_file.close()

        GlobalFunctions.print_status_of_run()

    def save_server_cmd_in_file(self, log_dir, server_cmd):
        # create file to fill running runs details
        my_file = open(log_dir + '/server_cmd.txt', 'w+')
        my_file.write(server_cmd)
        my_file.close()
