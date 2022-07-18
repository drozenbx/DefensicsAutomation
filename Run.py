#!/usr/bin/env python
import os
activate_this = os.path.expanduser("~/PycharmProjects/DefensicsAutomation/venv/bin/activate_this.py")
execfile(activate_this, dict(__file__=activate_this))

from DefensicsScript import *
from threading import Thread
from datetime import datetime
import GlobalVariables
import GlobalFunctions
import ReadEXCEL
import os


def add_ports():
    # ip-DUT,mac-DUT,ip-LP.mac-LP,name_device-LP,ipv6-DUT,ipv6-LP,10G
    #GlobalFunctions.add_port("10.100.10.100", "00:00:00:00:03:14", "10.100.10.200", "00:00:00:00:01:00", "cvl0_0",
    #                         "3001:1:3::1:10", "3001:1:3::1:20", "10G")
    GlobalFunctions.add_port("10.100.10.100", "00:00:00:00:03:14", "10.100.10.200", "00:00:00:00:01:00", "cvl0_0",
                             "fe80::200:ff:fe00:314", "fe80::200:ff:fe00:100", "10G")
    #GlobalFunctions.add_port("10.100.10.101", "00:02:00:01:03:15", "10.100.10.201", "00:00:00:00:01:01", "cvl0_1",
    #                         "fe80::202:ff:fe01:315", "fe80::200:ff:fe00:101", "10G")
    #GlobalFunctions.add_port("10.100.10.102", "00:03:00:02:03:16", "10.100.10.202", "00:00:00:00:01:02", "cvl0_2",
    #                         "fe80::203:ff:fe02:316", "fe80::200:ff:fe00:102", "10G")
    #GlobalFunctions.add_port("10.100.10.103", "00:04:00:03:03:17", "10.100.10.203", "00:00:00:00:01:03", "cvl0_3",
    #                         "fe80::204:ff:fe03:317", "fe80::200:ff:fe00:103", "10G")

    
    # lizysha: for MH tests
    #GlobalFunctions.add_port("133.133.10.10", "00:00:00:00:03:14", "133.133.10.20", "00:00:00:00:01:00", "cvl0_0",
      #                       "3001:1:3::1:10", "3001:1:3::1:20", "10G")

    #GlobalFunctions.add_port("10.100.10.101", "00:00:00:00:03:14", "10.100.10.201", "00:00:00:00:01:01", "cvl0_1",
     #                        "fe80::200:ff:fe00:101", "fe80::200:ff:fe00:201", "10G")

def init():

    # allow ssh to DUT machine
    GlobalFunctions.allow_ssh()

    add_ports()

    GlobalVariables.logger.info("Num of port: " + str(len(GlobalVariables.ports_list)))

    # ping all ports to see device aliveness
    GlobalFunctions.ping_all_ports(GlobalVariables.ports_list)

    # create background in order to run
    create_path_to_list_runs()


def run_regular_defensics_automation():
    # update date and time
    update_date()
    GlobalVariables.start_time = datetime.now()

    # create file to fill output log
    GlobalVariables.path_to_lists_runs_details = GlobalVariables.part_of_path_to_results + GlobalVariables.date + '_'\
                                                 + GlobalVariables.project

    if not os.path.exists(GlobalVariables.path_to_lists_runs_details):
        os.makedirs(GlobalVariables.path_to_lists_runs_details)

    # if run this script sign the run is regular run (not reproducing) - will take suites to run from XL
    message = "++++++++ REGULAR RUN - Running testplans from excel ++++++++\n"

    GlobalFunctions.enable_logging(message)

    # call init to initialize the run
    init()

    # create .txt files of CMDs from XL list of testplans to run
    ReadEXCEL.create_files_from_excel(GlobalVariables.path_to_XL, GlobalVariables.path_to_lists_runs_details
                                      + '/ListOfTestplans.txt', GlobalVariables.path_to_cmds_files,
                                      GlobalVariables.path_to_server_cmds_files)
    create_testplans_queue()
    create_threads_queue()

    # start the run by threads
    thread_run_regular_ports = Thread(target=start_run_regular_ports)
    thread_run_regular_ports.start()

    # Wait to all the running threads
    thread_run_regular_ports.join()
    for running_thread in GlobalVariables.running_threads_dic.values():
        running_thread.join()
        GlobalVariables.logger.info("did join to thread: " + str(running_thread.thread_id) + "-> "
                                    + str(running_thread.port.device_name))
        GlobalVariables.logger.info("all threads finished")

    # update and print status of run
    GlobalFunctions.print_status_of_run()

    # end - updates about the run and send results if need
    end_run("Regular Run")


def run_reproduce_defensics_automation(dics_cmd_device_reproduce):
    # update date and time
    update_date()
    GlobalVariables.start_time = datetime.now()

    # call init to initialize the run
    init()

    GlobalVariables.num_tests = len(dics_cmd_device_reproduce)
    GlobalVariables.logger.info("Tests to reproduce queue size is: " + str(GlobalVariables.num_tests) + "\n")

    # create a dictionary of available devices for reproducing of failures
    create_status_device_dic()

    # create threads queue to reproduce failures- every item is thread for one test
    create_reproduce_test_thread_queue(dics_cmd_device_reproduce)

    # start the run by threads
    thread_run_reproduce_runs = Thread(target=start_run_reproduce_runs)
    thread_run_reproduce_runs.start()
    # Wait to all the running threads
    thread_run_reproduce_runs.join()

    for running_thread in GlobalVariables.running_threads_dic.values():
        running_thread.join()
        GlobalVariables.logger.info("did join to thread: " + str(running_thread.thread_id) + "-> "
                                    + str(running_thread.port.device_name))
        GlobalVariables.logger.info("all threads finished")

    # update and print status of run
    GlobalFunctions.print_status_of_run()

    # end - updates about the run and send results if need
    end_run("Reproduce Failures")


if __name__ == '__main__':
    run_regular_defensics_automation()
