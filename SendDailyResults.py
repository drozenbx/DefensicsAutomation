#!/usr/bin/env python
import os
activate_this = os.path.expanduser("~/PycharmProjects/DefensicsAutomation/venv/bin/activate_this.py")
execfile(activate_this, dict(__file__=activate_this))

from datetime import datetime
import CheckAndSendResults
import GlobalVariables
import subprocess
import os


def send_daily_results(path, mail_title):
    """
    This function will send Daily results (if have)

    :param path: path to results directory
    :param mail_title: title of the mail to send
    """
    CheckAndSendResults.send_results(path, mail_title)


def check_run_currently_running(running_lines):
    i = 0
    detect_running = "ps -aux | grep java | grep testplan | grep {}.testplan | tr -s ' ' | cut -d ' ' -f 2"

    for line in running_lines:
        my_list = line.replace('\n', '').split(',')
        if i == 0 or len(my_list) < 2:
            i = 1
            continue
        name = my_list[1]

        proc = subprocess.Popen(detect_running.format(name), stdout=subprocess.PIPE, shell=True)
        output = proc.stdout.read().replace('\n', ',').split(',')

        if len(output) > 2:
            return name

    return None


def get_running_dir(list_dir):
    path_to_all_results = GlobalVariables.part_of_path_to_results
    list_results = []

    for item in list_dir:
        location_running = path_to_all_results + item + '/ListOfRunningRunsDetails.txt'

        if os.path.exists(location_running):
            list_results.append(item)

    # sort list of results
    list_results.sort()
    name_last_run = list_results[len(list_results) - 1]
    running_lines = open(path_to_all_results + name_last_run + '/ListOfRunningRunsDetails.txt', 'r').readlines()
    waiting_lines = open(path_to_all_results + name_last_run + '/ListOfWaitingRunsDetails.txt', 'r').readlines()

    if len(running_lines) > 1 or len(waiting_lines) > 0:
        found_running = check_run_currently_running(running_lines)
        if found_running is not None:
            print("Note: There are runs that run in background")
            return name_last_run

    return ''


def get_path_last_run():
    """
    This function will return the last results directory that was created today.
    """
    path_to_all_results = GlobalVariables.part_of_path_to_results
    list_today_results = []

    date = str(datetime.now())
    date = date[:date.find(' ')]

    for item in os.listdir(path_to_all_results):
        if date in item:
            list_today_results.append(item)

    if len(list_today_results) == 0:
        # if no run started today, check if run of other day still running
        path_to_last_result_today = get_running_dir(os.listdir(path_to_all_results))
        if path_to_last_result_today == '':
            print("\n=====No Automated Run ran today, and no one is running=====\n")
            exit()
    else:
        # sort list of results
        list_today_results.sort()

        path_to_last_result_today = list_today_results[len(list_today_results) - 1]

    print('\nLast result today-> ' + path_to_last_result_today)
    return path_to_all_results + '/' + path_to_last_result_today


if __name__ == '__main__':
    additional_txt_tittle = "Daily Results"

    path_to_current_run = get_path_last_run()
    send_daily_results(path_to_current_run, additional_txt_tittle)
