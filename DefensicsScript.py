import os
from MyPort import *
from threading import *
from datetime import datetime
from MyThread import MyThread
import MyTestPlan
import CheckAndSendResults
import time
import GlobalVariables
import GlobalFunctions


def create_path_to_list_runs():
    """
    This function create 3 files in the current results directory:
    1. ListOfWaitingRunsDetails - will be updated during the run about all WAITING tests details.
    2. ListOfRunningRunsDetails - will be updated during the run about all RUNNING tests details.
    3. ListOfFinishedRunsDetails - will be updated during the run about all FINISHED tests details.

    """
    # create file to fill tests that waiting to start run
    my_file = open(GlobalVariables.path_to_lists_runs_details + '/ListOfWaitingRunsDetails.txt', 'w+')
    my_file.write(GlobalVariables.LP_machine + ',' + GlobalVariables.project)
    my_file.close()

    # create file to fill running runs details
    my_file = open(GlobalVariables.path_to_lists_runs_details + '/ListOfRunningRunsDetails.txt', 'w+')
    my_file.write(GlobalVariables.LP_machine + ',' + GlobalVariables.project)
    my_file.close()

    # create file to fill finished runs details
    my_file = open(GlobalVariables.path_to_lists_runs_details + '/ListOfFinishedRunsDetails.txt', 'w+')
    my_file.write(GlobalVariables.LP_machine + ',' + GlobalVariables.project)
    my_file.close()

    # create file to fill the current runtime in case the run will suddenly stop
    GlobalFunctions.update_run_time()


def create_testplans_queue():
    """
    This function creates queue of testplans to run by the list of testplans from the XL.
    """
    try:
        f_list_names = open(GlobalVariables.path_to_lists_runs_details + '/ListOfTestplans.txt', 'r')
        list_name = f_list_names.readlines()

        with open(GlobalVariables.path_to_lists_runs_details + '/ListOfWaitingRunsDetails.txt', 'w') as f:

            for item in list_name:
                GlobalVariables.num_tests += 1
                my_list = item.replace('\n', '').split(',')
                protocol = my_list[0]
                name = my_list[1]
                giga = my_list[2]

                # add new waiting test to ListOfWaitingRunsDetails file
                f.write(item)

                if ('Client' in name or 'client' in name) and 'IEEE1588' not in name:
                    server_need_client = True
                else:
                    server_need_client = False

                # enter to regular queue of tests that can run on all the ports properly
                GlobalVariables.tests_queue.enqueue(MyTestPlan.MyTestPlan
                                                        (protocol, name, giga,
                                                         is_server_needed_client=server_need_client))

        GlobalVariables.logger.info("tests queue size is: " + str(GlobalVariables.num_tests) + "\n")

    except Exception as e:
        GlobalVariables.logger.error(e.message)


def create_threads_queue():
    """
    This function create threads queues for every device port
    (every thread will run on specific port)
    """
    try:
        # check if need to allocate regular thread for each port
        if GlobalVariables.num_tests < GlobalVariables.num_ports:
            num_regular_threads = GlobalVariables.num_tests
        else:
            num_regular_threads = GlobalVariables.num_ports

        for i in range(num_regular_threads):
            GlobalVariables.threads_queue.enqueue(MyThread(i, GlobalVariables.ports_list[i], reproduce_run=False))
        GlobalVariables.logger.info("Threads queue size is: " + str(GlobalVariables.threads_queue.size()) + "\n")

    except Exception as e:
        GlobalVariables.logger.error(e.message)


def create_status_device_dic():
    """
    *** FOR REPRODUCE OF FAILURES ONLY ***

    This function create a dictionary of available devices for reproducing of failures.
    every device is mapped to his status- Free or Busy will appear True or False

    """
    try:
        for i in range(len(GlobalVariables.ports_list)):
            port = GlobalVariables.ports_list[i]
            # TODO check every port if is available or not!!
            # create obj in dictionary for every port to check status
            if port.device_name not in GlobalVariables.status_devices_to_reproduce.keys():
                GlobalVariables.status_devices_to_reproduce[port.device_name] = True
            else:
                GlobalVariables.logger.info(port.device_name + " already exist")

    except Exception as e:
        GlobalVariables.logger.error(e.message)


def create_reproduce_test_thread_queue(dics_cmd_device_reproduce):
    """
    *** FOR REPRODUCE OF FAILURES ONLY ***

    This function creates a queue of threads- one thread for every test that need to be reproduce.

    :param dics_cmd_device_reproduce: a dictionary that contain
    all the details about the test to reproduce (cmd,device etc.)

    """
    try:
        device_port = {}
        waiting_list = [] #[GlobalVariables.LP_machine + ',' + GlobalVariables.project]

        # create dictionary that key is device name and value is his port
        for i in range(len(GlobalVariables.ports_list)):
            port = GlobalVariables.ports_list[i]
            device_port[port.device_name] = port

        # create queue of threads for all the tests that need reproduce of failures
        for test in dics_cmd_device_reproduce:

            # add new waiting test to ListOfWaitingRunsDetails file
            waiting_item = test["protocol"] + ',' + test["name"] + ',' + test["new_path"]
            waiting_list.append(waiting_item)

            # check if path doesn't exists or parameter wasn't found
            if "error" in test["device_name"]:
                GlobalVariables.logger.info("================================================================")
                GlobalVariables.logger.info("for test: " + test["name"])
                GlobalVariables.logger.info("ERROR - Had error when checked device that run this test run.")
                GlobalVariables.logger.info("path doesn't exists or parameter wasn't found")
                GlobalVariables.logger.info("================================================================")
                continue

            # check if device not in the list of available devices
            if test["device_name"] not in GlobalVariables.status_devices_to_reproduce.keys():
                GlobalVariables.logger.info("================================================================")
                GlobalVariables.logger.info("for test: " + test["name"])
                GlobalVariables.logger.info("ERROR - Had error when checked device that run this test run.")
                GlobalVariables.logger.info("device not in the list of available devices")
                GlobalVariables.logger.info("================================================================")
                continue

            new_thread = MyThread(test["name"], device_port[test["device_name"]],
                                           reproduce_run=True, dic_cmd=test)
            GlobalVariables.threads_test_reproduce_queue.enqueue(new_thread)

        with open(GlobalVariables.path_to_lists_runs_details + '/ListOfWaitingRunsDetails.txt', 'w') as f:
            for item in waiting_list:
                f.write(item + '\n')

    except Exception as e:
        GlobalVariables.logger.error(e.message)


def update_date():
    """
    This function update the current date & hour
    """
    date = str(datetime.now())
    date = date.replace(' ', '_')
    date = date.replace(':', '_')
    GlobalVariables.date = date


def start_run_regular_ports():
    """
    This function start the procedure of running regular Defensics run.
    the function will pop one by one the threads of "threads_queue" and will run them.
    if the threads queue is empty but the tests queue is not empty yet,the function
    will wait to threads to be free, then will continue the process.

    """
    try:
        if GlobalVariables.num_tests == 0:
            GlobalVariables.logger.info("\n======Any test need regular port======.\n")
            exit(0)
        elif GlobalVariables.threads_queue.is_empty() is True:
            GlobalVariables.logger.info("=======Tests need regular port! please configure regular port=======")
            exit(1)

        while GlobalVariables.tests_queue.is_empty() is False:
            while GlobalVariables.threads_queue.is_empty() is False:
                GlobalVariables.first_threads_lock.acquire()
                thread = GlobalVariables.threads_queue.dequeue()
                GlobalVariables.first_threads_lock.release()
                thread.start()

            # if need to wait for thread to continue magic runs
            if GlobalVariables.tests_queue.is_empty() is False:
                GlobalVariables.logger.info("\nRegular threads Queue is empty for now.\nwaiting........")
                GlobalFunctions.print_status_of_run()

                # TODO how much time the sleep??
                time.sleep(100)

        GlobalVariables.logger.info("\n====No Test Plan remain to run.====\n")
        GlobalFunctions.print_status_of_run()

    except Exception as e:
        GlobalVariables.logger.error(e.message)


def start_run_reproduce_runs():
    """
    *** FOR REPRODUCE OF FAILURES ONLY ***

    This function start the procedure of reproducing of failures.
    the function will pop one by one the threads of test in threads_test_reproduce_queue,
    if the need device is Free- will run the thread and continue, otherwise it will push
    again the thread to the end of the queue and this one will wait his turn again (and the device to be free).

    """
    try:
        while GlobalVariables.threads_test_reproduce_queue.is_empty() is False:
            GlobalVariables.tests_reproduce_lock.acquire()
            thread_to_run = GlobalVariables.threads_test_reproduce_queue.dequeue()
            GlobalVariables.tests_reproduce_lock.release()

            # in order to do join
            GlobalVariables.status_device_reproduce_lock.acquire()
            needed_device = thread_to_run.port.device_name

            if GlobalVariables.status_devices_to_reproduce[needed_device] is True:
                GlobalVariables.status_devices_to_reproduce[needed_device] = False
                thread_to_run.start()
                GlobalVariables.status_device_reproduce_lock.release()

            # if the device is busy- push again the test- wait for turn
            else:
                GlobalVariables.tests_reproduce_lock.acquire()
                GlobalVariables.threads_test_reproduce_queue.enqueue(thread_to_run)
                GlobalVariables.tests_reproduce_lock.release()

                GlobalVariables.logger.info("test " + thread_to_run.thread_id +
                                            " is waiting for " + needed_device + "......")
                GlobalVariables.status_device_reproduce_lock.release()

            time.sleep(50)

        GlobalVariables.logger.info("\n====No Test Plan that need reproduce of failures remain to run.====\n")
        GlobalFunctions.print_status_of_run()

    except Exception as e:
        GlobalVariables.logger.error(e.message)


def end_run(type_run):
    """
    This function end the process of Defensics Automated Run:
    will prepare the results and send them, print summary of the run etc.
    :param type_run: string that notify if the run was Regular or Reproducing of failures run.

    """
    # TODO what with reproduce queue??
    GlobalVariables.threads_queue.clear()
    CheckAndSendResults.send_results(GlobalVariables.path_to_lists_runs_details, type_run)
    GlobalVariables.logger.info("\n********************* finished successfully " + str(GlobalVariables.num_finished_tests) + " tests *********************")
    GlobalVariables.logger.info("(out of " + str(GlobalVariables.num_tests) + " tests)")
    GlobalVariables.logger.info("Time of run: " + str(GlobalVariables.current_time_of_run))

