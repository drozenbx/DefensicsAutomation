#!/usr/bin/env python
import os
activate_this = os.path.expanduser("~/PycharmProjects/DefensicsAutomation/venv/bin/activate_this.py")
execfile(activate_this, dict(__file__=activate_this))

import ReadXML
import GlobalVariables
import GlobalFunctions
import sys
from shutil import copyfile
from Run import run_reproduce_defensics_automation, add_ports

# full command line
# java -jar /opt/Synopsys/Defensics/monitor/boot.jar --rerun /root/synopsys/defensics/Automation_Results/
# 2018-08-27_14_44_38.490465_cvl/EAP-Server/EAP_Server_EAPol_Read_extra_identities/ --verdict "fail skip"
# --rerun-type index --rerun-preceding 10 --log-dir /root/synopsys/defensics/Automation_Results/
# 2018-08-27_14_44_38.490465_cvl/reproduce_failures/EAP-Server/EAP_Server_EAPol_Read_extra_identities/

str_fail = "failed-cases"
str_other = "other-cases"
str_pass = "passed-cases"

path_to_new_results_dir = ''


def get_device_name_from_log(old_path):
    """
    :param old_path: path to summary.txt- output of run that contains name of the device that run the current run.
    :return: device name of current path of run
    """
    device_name = ''
    line = ''

    if not os.path.exists(old_path + '/summary.txt'):
        device_name = "error- path to summary.txt doesn't exist!!"
    else:

        summary = open(old_path + '/summary.txt', 'r')
        lines = summary.readlines()
        my_line = ""
        my_interface_line = ""

        # TODO arrange this dirty code!!!!
        for line in lines:
            if "--device" in line or "--ldp-device" in line or "device=" in line:
                my_line = line
                break
            # for some protocols that didn't have device configured, for Ex. GTPv1-2
            if "interface" in line:
                my_interface_line = line
                break

        if my_line == "":
            device_name = "error- *device* parameter wasn't found in summary.txt!!"

            if my_interface_line == "":
                device_name = "error- *interface* parameter wasn't found in summary.txt!!"

            elif "--interface" in my_interface_line:
                ip = my_interface_line[my_interface_line.find('--interface '):]
                ip = ip[12:ip.find(' --')]
                device_name = GlobalFunctions.get_device_by_ip(ip)
                if device_name is None:
                    device_name = "error- ip: '" + ip + "' wasn't found in ports list!!"
        else:
            if "--device" in my_line:
                device_name = my_line[my_line.find('--device '):]
                device_name = device_name[9:device_name.find(' --')]

                if device_name[len(device_name) - 1] is ' ':
                    device_name = device_name[:device_name.find(' ')]

            elif "--ldp-device" in my_line:
                device_name = my_line[my_line.find('--ldp-device'):]
                device_name = device_name[13:device_name.find(' --')]

            elif "device=" in my_line:
                device_name = my_line[my_line.find('device='):]
                device_name = device_name[7:device_name.find(';')]

        summary.close()
    return device_name


def get_dics_cmds_device(list_dic_runs_result, num_to_repeat, num_of_timeout):
    """
    :param list_dic_runs_result: list of dictionaries of tests to reproduce.
            'dic_results': the dictionary with results from XML file
            'status': which reproduce this test need- fail, skip or both.
    :param num_to_repeat: num of time the user want to repeat every fail cases
    :param num_of_timeout: num of timeout the user want to between 2 fail cases
    :return: list of cmds to run results tests that need reproduce of failures, with the device_name thy used

    """
    try:
        num = 0

        dics_cmd_device_reproduce = []
        cmd_template = "java -jar /opt/Synopsys/Defensics/monitor/boot.jar --rerun {old_path} --verdict {status} \
                    --rerun-type index --rerun-preceding 10 --log-dir {new_path} --repeat {num_to_repeat}" \
                       " --timeout {num_of_timeout}"

        for item in list_dic_runs_result:
            num += 1
            cmd_to_run = cmd_template.format(old_path=item["old_path"], status=item["status"], new_path=item["new_path"]
                                             , num_to_repeat=num_to_repeat, num_of_timeout=num_of_timeout)
            device_name = get_device_name_from_log(item["old_path"])

            GlobalVariables.logger.info("\n" + str(num) + ") test: " + item["dic_results"]["name test"] +
                                        " need to be rerun on " + device_name + ".")
            GlobalVariables.logger.info("fail cases: " + str(item["dic_results"]["failed-cases"]))
            GlobalVariables.logger.info("other cases: " + str(item["dic_results"]["other-cases"]) + "\n")

            dic_cmd_device = {"cmd": cmd_to_run, "device_name": device_name, "protocol": item["dic_results"]["protocol"]
                , "name": item["dic_results"]["name test"], "old_path": item["old_path"], "new_path": item["new_path"]}

            dics_cmd_device_reproduce.append(dic_cmd_device)
            my_file = open(item["new_path"] + '/old-results-summary.txt', 'w+')
            my_file.write("FAILED: " + str(item["dic_results"]["failed-cases"]) + ", SKIP: " +
                          str(item["dic_results"]["other-cases"]))
            my_file.close()

        return dics_cmd_device_reproduce
    except Exception as e:
        GlobalVariables.logger.error(e.message)


def create_dir_results(path_to_list_results_to_reproduce):
    """
    This function create the new directory where new runs will enter - "reproduce_failures" directory

    :param path_to_list_results_to_reproduce: path to list of
    results to reproduce and create new directory of results
    """
    global path_to_new_results_dir

    new_results_dir = path_to_list_results_to_reproduce + '/reproduce_failures'

    # create a new dir where reproduced failures of testplans will appear
    if not os.path.exists(new_results_dir):
        os.makedirs(new_results_dir)
    else:
        print("This directory already have a 'reproduce_failures' directory.\n"
              "Please enter a new path or remove this directory.")
        exit()

    path_to_new_results_dir = new_results_dir


def create_new_dir_results(protocol, test_name):
    """
    This function create all the folders(directories) where new
    runs will enter under "reproduce_failures" directory

    :param path_to_list_results_to_reproduce: path to list of results to reproduce
    :param protocol: the protocol of current test to create new result directory
    :param test_name: the test name of current test to create new result directory

    """
    try:
        global path_to_new_results_dir
        new_results_dir = path_to_new_results_dir

        # create a new dir where reproduced failures of testplans will appear
        if not os.path.exists(new_results_dir):
            os.makedirs(new_results_dir)
        if not os.path.exists(new_results_dir + '/' + protocol):
            os.makedirs(new_results_dir + '/' + protocol)
        if not os.path.exists(new_results_dir + '/' + protocol + '/' + test_name):
            os.makedirs(new_results_dir + '/' + protocol + '/' + test_name)

        new_path = new_results_dir + '/' + protocol + '/' + test_name
        return new_path
    except Exception as e:
        GlobalVariables.logger.error(e.message)


def copy_server_cmd_to_reproduce_dir(list_dic_runs_result):
    """
    This function copy the old server_cmd file to the new directort of results.
    it will be used in next reproduce of failures.
    :param list_dic_runs_result: the list of all results that need reproduce of failures

    """
    for item in list_dic_runs_result:
        if ('Client' in item["dic_results"]["name test"] or 'client' in item["dic_results"]["name test"]) and \
                'IEEE1588' not in item["dic_results"]["name test"]:
            src = item["old_path"] + '/server_cmd.txt'
            dst = item["new_path"] + '/server_cmd.txt'

            copyfile(src, dst)


def create_output_log(path_to_list_results_to_reproduce):
    """
    This function create an output log for the reproduce of the failures
    :param path_to_list_results_to_reproduce: ath to list of results to reproduce

    """
    # create the big directory that will collect all the new results of reproducing
    create_dir_results(path_to_list_results_to_reproduce)

    # if output log has already been created exit the func
    if os.path.exists(path_to_list_results_to_reproduce + '/reproduce_failures/reproduce_output.log'):
        GlobalVariables.logger.warning("output file already exist.")
        exit()

    # get file to fill output log
    GlobalVariables.path_to_lists_runs_details = path_to_list_results_to_reproduce + '/reproduce_failures'

    GlobalFunctions.enable_logging("++++++++ REPRODUCE FAILURES RUN - Running testplans from results path  ++++++++\n")


def check_testplan_results(dir_name, subdir_name, reproduce_the_skips):
    """
    This function get details of results directory
    and check if those results need reproduce of failures

    :return: the function return a dictionary with the dic results and status of run

    """
    try:
        location = dir_name + '/' + subdir_name
        test_name = subdir_name
        list_dir = dir_name.split('/')
        protocol = list_dir[len(list_dir) - 1]
        date = list_dir[len(list_dir) - 2]
        date = date[:date.find('_')].replace('_', '')
        # TODO calculate time from readXML??
        time_run = "--:--:--"
        status = "\"pass\""
        new_path = ''
        dic = ReadXML.read_xml_results(location + "/run-time-info.xml", test_name, protocol, date, time_run)

        if "location doesn't exist" in dic["state"]:
            return None

        elif "stuck" in dic["state"]:
            GlobalVariables.logger.info('\n' + location)
            GlobalVariables.logger.info(dic['state'])
            GlobalVariables.logger.warning('Run was stuck- exiting.....')
            return None

        # if the user want to reproduce fail and skips cases -> reproduce_the_skips == 1
        elif reproduce_the_skips is '1' and int(dic[str_fail]) > 0 and int(dic[str_other]) > 0:
            status = "\"fail skip\""

        elif int(dic[str_fail] > 0):
            status = "\"fail\""

        # if the user want to reproduce only skips cases -> reproduce_the_skips == 1
        elif reproduce_the_skips is '1' and int(dic[str_other]) > 0:
            status = "\"skip\""

        if status is not "\"pass\"":
            new_path = create_new_dir_results(protocol, test_name)

        dic_test_reproduce = {"dic_results": dic, "status": status, "old_path": location, "new_path": new_path}
        return dic_test_reproduce
    except Exception as e:
        GlobalVariables.logger.error(e.message)


def get_list_dic_from_tree_directories(path_to_list_results_to_reproduce, reproduce_the_skips):
    """
    :param path_to_list_results_to_reproduce: path to list of results to reproduce
    :param reproduce_the_skips: 1 if the user want to reproduce also skips, and 0 if not
    :return: return a list with all the path to results of runs to reproduce

    """
    list_dic_runs_result = []
    is_main_dir = 1
    try:
        # traverse all the results directories of the required run to reproduce
        for dir_name, dir_names, files in os.walk(path_to_list_results_to_reproduce):
            # save in list only rhe runs that need reproduce of failures
            for subdir_name in dir_names:
                # don't save the first level directory -> protocols directories
                if is_main_dir == 0 and "reproduce_failures" not in subdir_name and 'not_to_reproduce_failures' not in dir_name:
                    dic_test_reproduce = check_testplan_results(dir_name, subdir_name, reproduce_the_skips)

                    if dic_test_reproduce is None:
                        name = dir_name[dir_name.rfind('/') + 1:]
                        GlobalVariables.logger.info("**test " + name + " didn't start to run (no results file)**\n")

                    elif "pass" in dic_test_reproduce["status"]:
                        GlobalVariables.logger.info("**test " + dic_test_reproduce["dic_results"]["name test"] +
                                                    " doesn't need reproduce of failures- it passed :)**\n")
                    else:
                        list_dic_runs_result.append(dic_test_reproduce)

            is_main_dir = 0
        return list_dic_runs_result
    except IOError as e:
        GlobalVariables.logger.error(e.message)


def reproduce_failures_of_runs(path_to_list_results_to_reproduce, reproduce_the_skips, num_of_repeat, num_of_timeout):
    """
    This function reproduce failures of specific run

    :param path_to_list_results_to_reproduce: path to list of results to reproduce
    :param reproduce_the_skips: 1 if the user want to reproduce also skips, and 0 if not
    :param num_of_repeat: num of time the user want to repeat every fail cases
    :param num_of_timeout: num of timeout the user want between 2 fail cases
    """

    try:
        # add ports in order to get able to check device name
        add_ports()

        # list of all runs path to reproduce
        list_dic_runs_result = get_list_dic_from_tree_directories(path_to_list_results_to_reproduce, reproduce_the_skips)

        # list of ready cmds to run
        dics_cmd_device_reproduce = get_dics_cmds_device(list_dic_runs_result, num_of_repeat, num_of_timeout)

        # copy server_cmd.txt to new directory result
        copy_server_cmd_to_reproduce_dir(list_dic_runs_result)

        # run the cmds in Automation Script (./Run)
        run_reproduce_defensics_automation(dics_cmd_device_reproduce)

    except Exception as e:
        GlobalVariables.logger.error(e.message)


if __name__ == '__main__':
    if len(sys.argv) <= 4:
        print ("Please enter ^results directory^, ^reproduce skips?^ (answer 1 or 0)" \
              ", num of ^repeat^ you want for fail/other cases, and ^timeout^ between cases")
    else:
        global_results_path = sys.argv[1]
        reproduce_skips = sys.argv[2]
        num_repeat = sys.argv[3]
        num_timeout = sys.argv[4]
        create_output_log(global_results_path)

        reproduce_failures_of_runs(global_results_path, reproduce_skips, num_repeat, num_timeout)
        additional_txt_tittle = "Reproduce Failures"

    # path = "/root/synopsys/defensics/Automation_Results/2018-09-20_16_47_12.068182_fvl"
    # reproduce_failures_of_runs(path, 1)
