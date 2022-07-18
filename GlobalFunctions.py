from ManageLogging import ColoredLogger
from datetime import datetime, timedelta
from ExecuteAsInstrumentation import check_device_status_for_external_use
import GlobalVariables
import subprocess
import logging
import MyPort
import pexpect
import os


def create_logger(name_logger):
    """
    This function create a logger that will copy run output to log in current results directory.
    """
    try:
        if not os.path.exists(GlobalVariables.path_to_lists_runs_details + '/' + name_logger):
            print("\nDIRECTORY OUTPUT " + GlobalVariables.path_to_lists_runs_details + '/' + name_logger)
            my_file = open(GlobalVariables.path_to_lists_runs_details + '/' + name_logger, 'w+')
            my_file.write("My Defensics Run \n")
            my_file.close()

        if 'server' in name_logger:
            GlobalVariables.path_to_save_server_log = GlobalVariables.path_to_lists_runs_details + '/' + name_logger
        else:
            GlobalVariables.path_to_save_log = GlobalVariables.path_to_lists_runs_details + '/' + name_logger

    except Exception as e:
        print(e.message)


def enable_logging(message_run):
    # enable logging
    logging.setLoggerClass(ColoredLogger)
    if "REGULAR" in message_run:
        create_logger("regular_output.log")
    elif "REPRODUCE" in message_run:
        create_logger("reproduce_output.log")
    else:
        create_logger("output.log")

    GlobalVariables.logger = logging.getLogger(GlobalVariables.path_to_save_log)

    GlobalVariables.logger.critical(message_run)


def add_port(ip, mac, virtual_ip, virtual_mac, device_name, ipv6, ipv6_LP, giga):
    """
    This function get ports details and create a new port in "ports_list"
    """
    # check if port doesn't exist
    for port in GlobalVariables.ports_list:
        if port.ip == ip:
            GlobalVariables.logger.info("port '" + ip + "' already exist.")
            return

    port = MyPort.MyPort(ip, mac, virtual_ip, virtual_mac, device_name, ipv6, ipv6_LP, giga)
    GlobalVariables.ports_list.append(port)
    GlobalVariables.num_ports += 1


def print_status_of_run():
    """
    This function print status of run: nuber of finished and running tests,
    current time of run, and a check of ping to all the ports to see aliveness.

    """
    GlobalVariables.logger.info("\n***status of run: " + str(GlobalVariables.num_finished_tests) + "/" +
                                str(GlobalVariables.num_tests) + " tests finished, " +
                                str(GlobalVariables.num_running_tests) + "/" + str(GlobalVariables.num_tests) +
                                " tests are running.***")

    update_run_time()
    GlobalVariables.logger.info("current time of run: " + str(GlobalVariables.current_time_of_run) + "\n")
    status = ping_all_ports(GlobalVariables.ports_list)


def update_run_time():
    """
    This function update current run time in the file and in the global variable.
    """
    GlobalVariables.current_time_of_run = get_time(GlobalVariables.start_time)
    my_file = open(GlobalVariables.path_to_lists_runs_details + '/RunTime.txt', 'w+')
    my_file.write(str(GlobalVariables.current_time_of_run) + ".")
    my_file.close()


def ssh_copy_id():
    user = GlobalVariables.dut_user
    password = GlobalVariables.dut_password
    DUT_machine = GlobalVariables.DUT_machine

    str_ssh = '/usr/bin/ssh-copy-id  -i {} {}@{}'.format('/{}/.ssh/id_rsa.pub'.format(user), user, DUT_machine)
    child = pexpect.spawn(str_ssh)
    try:
        index = child.expect(['continue connecting \(yes/no\)',
                              '{}@{}\'s password:'.format(user, DUT_machine), pexpect.EOF], timeout=20)
        print str(index)

        if index == 0:
            child.sendline('yes')
            print(child.after, child.before)
            index = child.expect(['continue connecting \(yes/no\)', 'password:', pexpect.EOF], timeout=20)

        # if the ssh-copy-id ask 2 times to allow the ssh - and wait for 'yes',
        if index == 0:
            child.sendline('yes')
            print(child.after, child.before)
            index = child.expect(['continue connecting \(yes/no\)', 'password:', pexpect.EOF], timeout=20)
        if index == 1:
            child.sendline(password)
            print(child.after, child.before)
            index = child.expect(['continue connecting \(yes/no\)', 'password:', pexpect.EOF], timeout=20)

        if index == 2:
            print('[ key to {} exists ]'.format(DUT_machine))
            print(child.after, child.before)

        child.close()
    except pexpect.TIMEOUT:
        print(child.after, child.before)
        child.close()
    else:
        print('finished, ready')


def ssh_keygen():
    password = GlobalVariables.dut_password
    ssh = 'ssh-keygen -t rsa'
    child = pexpect.spawn(ssh)
    try:
        index = child.expect(['(/root/.ssh/id_rsa):',
                              'Overwrite (y/n)?', '(empty for no passphrase):',
                              'Enter same passphrase again:', pexpect.EOF], timeout=20)
        print str(index)

        if index == 0:
            child.sendline()
            print(child.after, child.before)
            index = child.expect(['(/root/.ssh/id_rsa):',
                                  'Overwrite (y/n)?', '(empty for no passphrase):',
                                  'Enter same passphrase again:', pexpect.EOF], timeout=20)

        if index == 1:
            child.sendline(password)
            print(child.after, child.before)
            index = child.expect(['(/root/.ssh/id_rsa):',
                                  'Overwrite (y/n)?', '(empty for no passphrase):',
                                  'Enter same passphrase again:', pexpect.EOF], timeout=20)
        if index == 2:
            child.sendline(password)
            print(child.after, child.before)
            index = child.expect(['(/root/.ssh/id_rsa):',
                                  'Overwrite (y/n)?', '(empty for no passphrase):',
                                  'Enter same passphrase again:', pexpect.EOF], timeout=20)

        if index == 3:
            child.sendline(password)
            print(child.after, child.before)
            index = child.expect(['(/root/.ssh/id_rsa):',
                                  'Overwrite (y/n)?', '(empty for no passphrase):',
                                  'Enter same passphrase again:', pexpect.EOF], timeout=20)

        child.close()
    except pexpect.TIMEOUT:
        print(child.after, child.before)
        child.close()


def allow_ssh():
    """
    This function will allow ssh to be automatic without password to DUT machine.
    (in order to run sever Defensics CMD)
    """
    try:
        subprocess.call('ssh-add', shell=True)
        subprocess.call('eval "$(ssh-agent -s)"', shell=True)

        # TODO need sometimes to run it also in order to allow ssh?? it take a lot of to run time... :(
        # ssh_keygen()
        ssh_copy_id()
    except Exception as e:
        print(e.message)


def do_process(str_ping, f_null):
    """
    Do ping process but don't save results and don't print
    :param str_ping: string of the ping to cmd to run
    :param f_null: null file
    :return: results of the process
    """
    process = -1
    try:
        # do ping CMD
        process = subprocess.call(str_ping, stdout=f_null, stderr=subprocess.STDOUT, shell=True)
    except Exception as e:
        GlobalVariables.logger.error(e.message)

    return process


def ping_all_ports(ports_list):
    """
    This Function get a list of ports, and need to check if there is ping to every port in the list.
    :param ports_list: list of the ports to check ping
    """
    is_first_fail_ping = 1
    status = 0

    for port in ports_list:
        # str_ping = 'ping -c 1 -I {} {}'.format(port.device_name, port.ip)
        str_ping = 'ping -c 1 {}'.format(port.ip)
        f_null = open(os.devnull, 'w')

        process = do_process(str_ping, f_null)

        if process == 0:
            GlobalVariables.logger.info("ping to " + port.ip + " passed")

        # if ping failed
        if process != 0:
            # if current ping is first to fail
            if is_first_fail_ping == 1:
                is_first_fail_ping = 0
                GlobalVariables.logger.error("====================================")
                GlobalVariables.logger.error("=========PROBLEMS IN PING!!=========")
                GlobalVariables.logger.error("====================================")
                status = -1
            GlobalVariables.logger.error("ERROR - no rout to host " + port.ip)
            check_device_status_for_external_use(port.device_name, port.ip, 1)

        # if specific ping passed but other before not- Note this (because it's probably sign that ping work now)
        elif is_first_fail_ping == 0:
            GlobalVariables.logger.info("ping to " + port.ip + " passed")
            status = 0

        else:
            str_ping = 'ping6 -c 1 -I {} {}'.format(port.device_name, port.ipv6)
            process = do_process(str_ping, f_null)
            if process != 0:
                GlobalVariables.logger.error("======== PROBLEMS IN PING 6 ONLY!!======== (" + port.device_name + ")")
                status = -2

    # if all ping past successfully
    if is_first_fail_ping == 1:
        GlobalVariables.logger.info("ping to ports pass successfully :)")
        status = 0
    # else, try to send valid packet
    # else:
    #     port_check = GlobalVariables.ports_list[0]
    #     check_device_status_for_external_use(port_check.device_name, port_check.ip, 1)

    return status


def get_time(start_time):
    """
    This function get start time, calculate and return how much time has passed since then
    :param start_time: a time variable with some time
    :return: how much time has passed from start_time since then
    """
    try:
        end_time = datetime.now()

        s1 = str(start_time.year) + '/' + str(start_time.month) + '/' + str(start_time.day) + ' ' + \
             str(start_time.hour) + ':' + str(start_time.minute) + ':' + str(start_time.second)
        s2 = str(end_time.year) + '/' + str(end_time.month) + '/' + str(end_time.day) + ' ' + \
             str(end_time.hour) + ':' + str(end_time.minute) + ':' + str(end_time.second)
        FMT = '%Y/%m/%d %H:%M:%S'

        return datetime.strptime(s2, FMT) - datetime.strptime(s1, FMT)
    except Exception as e:
        GlobalVariables.logger.error(e.message)


def get_time_from_file(global_path, is_for_seconds=0):
    running_line = None
    if not os.path.exists(global_path + '/RunTime.txt'):
        return '--:--:--'

    lines = open(global_path + '/RunTime.txt', 'r').readlines()

    for line in lines:
        if 'running' in line:
            running_line = line
            # break

    if running_line is None:
        return '--:--:--'

    if is_for_seconds == 0:
        return running_line[running_line.find('=') + 1:]

    return running_line[running_line.find('-') + 1:running_line.find('|')]


def get_hours_min_sec(time):
    l_time = []
    hours = 0
    time = str(time)

    if 'day' in time:
        days = time[:time.find(' day')]
        hours = int(days) * 24
        time = time[time.find(', ') + 2:]

    time = time.split(':')

    l_time.append(hours + int(time[0]))
    l_time.append(int(time[1]))
    l_time.append(int(time[2]))

    return l_time


def sum_time(time1, time2, name):
    try:
        try:
            t1 = time1
            t2 = time2
            time1 = get_hours_min_sec(time1)
            time2 = get_hours_min_sec(time2)
        except:
            GlobalVariables.logger.error(name + " did problem with time:")
            GlobalVariables.logger.error(time1)
            GlobalVariables.logger.error(time2)

        new_time = timedelta(hours=int(time1[0]), minutes=int(time1[1]), seconds=int(time1[2])) + \
                   timedelta(hours=int(time2[0]), minutes=int(time2[1]), seconds=int(time2[2]))

        return str(new_time)
    except Exception as e:
        GlobalVariables.logger.error(e.message)


def update_server_cycle():

    server = GlobalVariables.server_machine
    if not os.path.exists('/net/{0}/root/PycharmProjects/DefensicsAutomation/UpdateCycleResults.py'.format(server)):
        GlobalVariables.logger.info('ERROR - Script to update cycle in server not exist!!!!!!'
                                    '\n please update server.............')
        return -1

    # run remote update of cycle in server
    process = subprocess.call('/net/{0}/root/PycharmProjects/DefensicsAutomation/UpdateCycleResults.py'.format(server),
                              shell=True, stderr=subprocess.PIPE)

    if process == 0:
        GlobalVariables.logger.info('Server Cycle up-to-date :)\n')
    else:
        GlobalVariables.logger.info('Server Cycle update FAILED.\n'
                                    'please run UpdateCycleResults.py script in server machine.\n')
        return -1
    return 0


def get_device_by_ip(ip):
    for port in GlobalVariables.ports_list:
        if str(port.virtual_ip) == ip:
            return port.device_name
    return None
