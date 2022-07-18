from datetime import datetime
from tabulate import tabulate

import os

import GlobalFunctions
import ReadXML
import GlobalVariables
import email_utils

str_pass_casses = 'passed-cases'
str_fail_casses = 'failed-cases'
str_other_casses = 'other-cases'
str_remaining_casses = 'remaining-cases'
all_status = {'pass': 0, 'fail': 0, 'other': 0, 'stuck': 0}

str_pass = 'pass'
str_fail = 'fail'
str_other = 'other'
str_stuck = 'stuck'
table_results = None

project = ''
num_tests = 0
num_finished_tests = 0
num_running_tests = 0
num_waiting_tests = 0
html_to_write_finished = ''
html_to_write_running = ''

table_to_write = []


def read_run_time_from_file(location_list_results):
    """
    This function read and return the updated run time from "RunTime" file
    :param location_list_results: location of "RunTime" file
    :return: current run time of test run

    """
    # read current run time from the saved file
    if os.stat(location_list_results + '/RunTime.txt').st_size <= 0:
        exit()

    my_file = open(location_list_results + '/RunTime.txt', 'r')

    line = my_file.readline()
    my_list = line.replace('\n', '').split('.')
    run_time = my_list[0]
    my_file.close()

    return run_time


def send_email(all_status_dic, my_file, additional_txt_tittle):
    """
    This function send an e-mail of results for all the people in recipients list
    :param all_status_dic: dictionary of all the results
    :param my_file: an html file contain all the message body
    :param additional_txt_tittle: for e-mail title
    :return:
    """
    try:
        recipients_file = GlobalVariables.path_to_recipients_file
        directory = os.path.abspath(os.path.dirname(__file__))

        # taking numbers of success/ failures/ other
        num_passed = all_status_dic[str_pass]
        num_failed = all_status_dic[str_fail]
        num_other = all_status_dic[str_other]
        num_stuck = all_status_dic[str_stuck]

        # reading recipients list from file
        with open(recipients_file, 'rb') as fp:
            recipients_list = fp.read().splitlines()

        email_utils.email_to = recipients_list
        quick_results = project + ' - ' + str(num_passed) + ' | ' + str(num_other) + ' | ' + str(num_failed) + ' | ' \
                        + str(num_stuck) + ' -> ' + additional_txt_tittle

        message = email_utils.create_message(quick_results)

        my_file = os.path.join(directory, my_file)
        with open(my_file) as f:
            html = f.read()
        email_utils.set_body(message, html)
        email_utils.send_email(message, recipients_list)

        GlobalVariables.logger.info("Successfully sent:)\n")
        GlobalVariables.logger.info("Table of results:")
        GlobalVariables.logger.info(
            tabulate(table_results, headers=['Num', 'Protocol\Name', 'Time', 'Status'], tablefmt='orgtbl'))
        GlobalVariables.logger.info("\n")

    except Exception as e:
        GlobalVariables.logger.error(e.message)


def send_results(location_list_results, additional_txt_tittle):
    """
    This function send results of run.

    :param location_list_results: path to results directory. (where lists of results are)
    :param additional_txt_tittle: the title we want to see in the e-mail:
           'Regular Run' or 'Reproduce Run'. (depending on the current run)

    """
    GlobalVariables.path_to_lists_runs_details = location_list_results
    GlobalFunctions.enable_logging('')

    # update server cycle
    status = GlobalFunctions.update_server_cycle()

    if status == -1:
        GlobalVariables.logger.info("###FYI- ERROR had occurred during update of server Cycle!!!###")

    path_to_result_file = write_results_to_file(location_list_results)
    send_email(all_status, path_to_result_file, additional_txt_tittle)


def check_ping():
    """
    This function check ping status to update that in the mail
    :return: string that explain if there are problems of ping or not.
    """
    ping_str = ''
    status = GlobalFunctions.ping_all_ports(GlobalVariables.ports_list)

    if status == -1:
        ping_str = '<br /><h3>=========PROBLEMS IN PING!!=========</h3>'
    elif status == -2:
        ping_str = '<br /><h3>=========PROBLEMS IN PING 6 ONLY!!=========</h3>'

    return ping_str


def write_results_to_file(location_list_results):
    """
    This function write results of run into a file.
    :param location_list_results: location of the results where the new results file will be saved

    """
    try:
        global num_tests
        global num_running_tests
        global num_finished_tests
        global num_waiting_tests
        global location_finished
        global location_running
        global project
        global LP
        global table_to_write
        global html_to_write_finished
        global html_to_write_running
        global table_results

        location_finished = location_list_results + "/ListOfFinishedRunsDetails.txt"
        location_running = location_list_results + "/ListOfRunningRunsDetails.txt"
        location_waiting = location_list_results + "/ListOfWaitingRunsDetails.txt"

        my_file = ''
        run_time = str(read_run_time_from_file(location_list_results))

        if os.stat(location_finished).st_size > 0:
            my_file = open(location_finished, 'r')
        elif os.stat(location_running).st_size > 0:
            my_file = open(location_running, 'r')
        elif os.stat(location_waiting).st_size > 0:
            my_file = open(location_waiting, 'r')
            GlobalVariables.logger.info("==No run started==")
        else:
            GlobalVariables.logger.info("==Any test ran==")
            exit()

        line = my_file.readline()

        my_list = line.replace('\n', '').split(',')
        LP = my_list[0]
        project = my_list[1]
        my_file.close()

        now = str(datetime.now())
        now = now.replace(' ', '_')
        now = now.replace(':', '_')

        path_to_file = location_list_results + '/' + now + '_' + project + '_Results'

        # ping all ports to see device aliveness and update mail
        str_ping_status = check_ping()

        GlobalVariables.logger.info("\nPublish Results....")

        # TODO 751 server used?
        finished_table = aggregate_tests(location_finished, "ladj751??")
        running_table = aggregate_tests(location_running, "ladj751??")
        waiting_table = aggregate_tests_not_start(location_waiting)

        with open(path_to_file + '.html', 'w') as html_file:
            html_file.write('<html><head>')

            # link the javascript file to your html using the <script> tag
            html_file.write('<script src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.10.1/moment.min.js">'
                            '</script><script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js">'
                            '</script>')

            html_file.write('<title>Defensics Automated run</title>')
            html_file.write('</head><body><h1>')
            html_file.write('Defensics Automated run')
            html_file.write('</h1>\n\n<h3>(Title template: PASS | SKIP | FAIL | STUCK )' + str_ping_status)
            html_file.write('</h3>\n\n<pre>')

            html_file.write("\nRunning time of automated run is: " + run_time)
            html_file.write("\nMachine name (LP): " + LP)
            html_file.write("\nResults path: " + location_list_results)

            # update table results
            table_results = table_to_write

            if finished_table is not '' or running_table is not '' or waiting_table is not '':
                # insert table results in HTML string
                html_file.write('</pre>\n\n<br /><table><tr>\n')
                html_file.write('<td bgcolor="gray"><font color="white"># &nbsp&nbsp&nbsp&nbsp</font></td>')
                html_file.write('<td bgcolor="gray"><font color="white">Protocol &nbsp/&nbsp Name Test '
                                '&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp</font></td>')
                html_file.write('<td bgcolor="gray" align="right"><font color="white">Time &nbsp&nbsp&nbsp</font></td>')
                html_file.write('<td bgcolor="gray"><font color="white">Status &nbsp</font></td>')
                html_file.write(finished_table)
                html_file.write(running_table)
                html_file.write(waiting_table)
                html_file.write('</table>\n')
                html_file.write('</b></pre><br /><br />\n\n')

            # checking if some test ran
            if num_tests == 0:
                GlobalVariables.logger.info("==any test ran, no results to send==")
                exit()

            passed_percent = int((all_status['pass'] * 100.0) / num_tests)
            other_percent = int((all_status['other'] * 100.0) / num_tests)
            stuck_percent = int((all_status['stuck'] * 100.0) / num_tests)
            failed_percent = int((all_status['fail'] * 100.0) / num_tests)

            html_file.write("\n\n\n<table><tr><td>number of tests passed " + str(all_status['pass']) + "</td><td>[ "
                            + str(passed_percent) + "% PASS ]</td></tr>")
            html_file.write(
                "\n<tr><td>number of tests other-skip " + str(all_status['other']) + "</td><td>[ " + str(other_percent)
                + "% SKIP ]</td></tr>")
            html_file.write("\n<tr><td>number of tests stuck " + str(all_status['stuck']) + "</td><td>[ " + str(
                stuck_percent) + "% STUCK ]</td></tr>")
            html_file.write("\n<tr><td>number of tests failed " + str(all_status['fail']) + "</td><td>[ " + str(
                failed_percent) + "% FAIL ]</td></tr>")
            html_file.write("\n<tr><td>----------------------------------</td></tr>")
            html_file.write("\n<tr><td>number of tests: </td><td>" + str(num_tests) + "</td></tr>")
            html_file.write("\n\t<tr><td>number of finished tests: </td><td>" + str(num_finished_tests) + "</td></tr>")
            html_file.write("\n\t<tr><td>number of running tests: </td><td>" + str(num_running_tests) + "</td></tr>")
            html_file.write("\n\t<tr><td>number of waiting tests: </td><td>" + str(num_waiting_tests) +
                            "</td></tr></table>")

            html_file.write("<br /><br /><h2 >List of results of runs: </h2>")

            # write result of all *finished* runs
            html_file.write(html_to_write_finished)

            # write result of all runs that where *running* and didn't finish
            html_file.write(html_to_write_running)

            html_file.write('</ br><b>Total run time: ' + run_time + '</b></ br>')
            html_file.write('</body></html>')

        return path_to_file + '.html'
    except Exception as e:
        GlobalVariables.logger.error(e.message)


# #TODO
# # ==================================================================================================
# def generate_chart():
#     (passed, failed, errors, disabled) = count_test_states()
#
#     # Also calculate percentages
#     total = passed + failed + errors + disabled
#     percent_passed = int(round(100.0 * passed / total))
#     percent_failed = int(round(100.0 * failed / total))
#     percent_errors = int(round(100.0 * errors / total))
#     percent_disabled = int(round(100.0 * disabled / total))
#
#     # Use Google Charts' old (non-JavaScript) API
#     url = 'https://chart.googleapis.com/chart?chs=445x225&cht=p&chd=t:{0},{1},{2},{3}'
#     url += '&chl=Passed {0} ({4}%)|Failed {1} ({5}%)|Error {2} ({6}%)|Disabled {3} ({7}%)'
#     url = url.format(passed, failed, errors, disabled, percent_passed, percent_failed,percent_errors,percent_disabled)
#
#     return '<p><img src="{}" width="445" height="225" alt="Pie Chart" />'.format(url)
#
# # ==================================================================================================


def aggregate_tests(location_file, server_dir):
    try:
        global num_tests
        global num_running_tests
        global num_finished_tests
        global table_to_write
        global html_to_write_finished
        global html_to_write_running
        global LP
        i = 0
        old_status = ''
        html = ''
        html_full_results = ''
        href = '<a href="#{}" style="color:white">{}'

        if os.stat(location_file).st_size <= 0:
            return ''

        with open(location_file) as my_file:
            for line in my_file:
                my_list = line.replace('\n', '').split(',')
                if i == 0 or my_list[0] == '':
                    i = 1
                    continue
                num_tests += 1

                path_to_results_or_fail_msg = my_list[0]
                global_path = path_to_results_or_fail_msg[:path_to_results_or_fail_msg.find('run-time-info.xml')]
                test_name = my_list[1]
                test_protocol = my_list[2]
                date = str(my_list[3])
                time_run = str(my_list[4])
                if 'day' in time_run:
                    time_run += ',' + str(my_list[5])

                # time_run = GlobalFunctions.get_time_from_file(global_path)

                title = test_protocol + '/<b>' + test_name

                # if test ran didn't finish with 0 -> sign that run works -> don't check the results in file
                if "test failed during run" in path_to_results_or_fail_msg:
                    all_status['stuck'] = all_status['stuck'] + 1
                    html += '\n<tr><td>{}.</td><td>{}</b></td><td align="right">{}</td>' \
                        .format(num_tests, title, '(--:--:--)')
                    html += '<td bgcolor="black"><font color="white">' + href.format(num_tests, "ERROR") + '</a></font>'
                    html += '</td></tr>\n'
                    html_full_results += ('\n<b><a name={}></a>'.format(num_tests) + str(
                        num_tests) + ") Test " + test_name + " </b>(" + test_protocol +
                                          ") - <font color='black'>" + path_to_results_or_fail_msg + "</font>")
                    html_full_results += "<br />______________________________________________________" \
                                         "_______________________<br /><br />"
                    table_to_write.append([str(num_tests), test_protocol + '\\' + test_name, time_run, 'stuck'])
                    continue
                else:
                    if "stuck" in time_run:
                        # test didn't move from RunningRuns file to FinishedRuns file
                        num_running_tests += 1
                        old_status = time_run
                        time_run = GlobalFunctions.get_time_from_file(global_path)
                        # duration = '(--:--:--)'
                    else:
                        num_finished_tests += 1
                        # duration = time_run[:time_run.rindex(':')]

                    duration = '({})'.format(time_run)

                    html += '\n<tr><td>{}.</td><td>{}</b></td><td align="right">{}</td>' \
                        .format(num_tests, title, duration)

                    item = ReadXML.read_xml_results(path_to_results_or_fail_msg, test_name,
                                                    test_protocol, date, time_run)
                    # " --report html --output " + GlobalVariables.part_of_path_to_results + self.protocol + '/'
                    path_log_file = LP + ': ' + path_to_results_or_fail_msg

                    # taking numbers of success/ errors/ failures
                    num_passed = item[str_pass_casses]
                    num_failed = item[str_fail_casses]
                    num_other = item[str_other_casses]
                    num_remaining = item[str_remaining_casses]

                    if "stuck" in old_status:
                        all_status['stuck'] = all_status['stuck'] + 1
                        test_status = 'the run was STOPPED'
                        html += '<td bgcolor="blue"><font color="white">' + href.format(num_tests, "STOPPED") + \
                                '</a></font>'
                        status_font = '<font color="blue">'

                    elif num_other == 0 and num_passed == 0 and num_failed == 0 \
                            or num_remaining != 0:
                        all_status['stuck'] = all_status['stuck'] + 1
                        test_status = 'finished STUCK'
                        html += '<td bgcolor="black"><font color="white">' + href.format(num_tests, "ERROR") + \
                                '</a></font>'
                        status_font = '<font color="black">'

                    elif num_failed > 0:
                        all_status['fail'] = all_status['fail'] + 1
                        test_status = 'FAILED'
                        html += '<td bgcolor="red"><font color="white">' + href.format(num_tests, "FAIL") + \
                                '</a></font>'
                        status_font = '<font color="red">'

                    elif num_other > 0:
                        all_status['other'] = all_status['other'] + 1
                        test_status = 'with SKIPS'
                        html += '<td bgcolor="orange"><font color="white">' + href.format(num_tests, "SKIP") + \
                                '</a></font>'
                        status_font = '<font color="orange">'

                    else:
                        all_status['pass'] = all_status['pass'] + 1
                        test_status = 'PASS'
                        html += '<td bgcolor="green"><font color="white">' + href.format(num_tests, "PASS") + \
                                '</a></font>'
                        status_font = '<font color="green">'

                    table_to_write.append([str(num_tests), item['protocol'] + '\\' + item["name test"],
                                           duration[1:len(duration) - 2], test_status])
                    html_full_results += ('\n<b><a name={}></a>'.format(num_tests) + str(num_tests) + ") Test " +
                                          item["name test"] + "</b> (" + item['protocol'] + ") - " + status_font +
                                          '<b>' + test_status + "</b></font>")
                    html_full_results += ("<br />" + 'run-time' + ": " + str(item['run-time']))
                    html_full_results += ("<br />" + 'state' + ": " + item['state'])

                    if "reproduce_failures" in location_file:
                        f = open(global_path + "/old-results-summary.txt", "r")
                        my_line = f.readline()
                        html_full_results += "<br />(old results where -> " + my_line + ")"

                    html_full_results += ("<br />" + str_pass_casses + ": " + str(num_passed))
                    html_full_results += ("<br />" + str_other_casses + ": " + str(num_other))
                    html_full_results += ("<br />" + str_fail_casses + ": " + str(num_failed))
                    html_full_results += ("<br />" + str_remaining_casses + ": " + str(num_remaining))
                    html_full_results += ("<br />link to log: " + path_log_file)
                    html_full_results += "<br />______________________________________________________" \
                                         "_______________________<br /><br />"

                    # if show_log:
                    #     html += '</td><td><a href="http://{}/logs/{}/{}.html">Log</a>'.format(server_host, server_dir,
                    #                                                                           file_name)
                    # if show_owner:
                    #     html += ' - Owner: ' + owners.get(title.replace('<b>', ''), '???')

                    html += '</td></tr>\n'

        if 'Finished' in location_file:
            html_to_write_finished = html_full_results
        else:
            html_to_write_running = html_full_results

        return html
    except Exception as e:
        GlobalVariables.logger.error(e.message)


def aggregate_tests_not_start(location_waiting):
    try:
        global num_waiting_tests
        global num_tests
        html = ''
        i = 0

        if os.stat(location_waiting).st_size <= 0:
            return ''

        with open(location_waiting) as my_file:
            for line in my_file:
                my_list = line.replace('\n', '').split(',')
                # if i == 0 or my_list[0] == '':
                #     i = 1
                #     continue
                num_tests += 1
                num_waiting_tests += 1

                protocol = my_list[0]
                name = my_list[1]

                title = protocol + '/<b>' + name
                html += '\n<tr><td>{}.</td><td>{}</b></td><td align="right">{}</td>' \
                    .format(num_tests, title, "(--:--:--)")

                all_status['stuck'] = all_status['stuck'] + 1
                html += '<td bgcolor="gray"><font color="white">NO RUN</font>'

                table_to_write.append([str(num_tests), protocol + '\\' + name, "--:--:--", "NO RUN"])
                html += '</td></tr>\n'

        return html

    except Exception as e:
        GlobalVariables.logger.error(e.message)
