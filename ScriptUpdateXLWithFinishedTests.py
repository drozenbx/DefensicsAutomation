#!/usr/bin/env python
import os
activate_this = os.path.expanduser("~/PycharmProjects/DefensicsAutomation/venv/bin/activate_this.py")
execfile(activate_this, dict(__file__=activate_this))
import ReadEXCEL
import GlobalVariables
import GlobalFunctions
import ReadXML
import sys


str_pass_casses = 'passed-cases'
str_fail_casses = 'failed-cases'
str_other_casses = 'other-cases'
str_remaining_casses = 'remaining-cases'


def update_XL_table(location_file):

    try:
        i = 0
        old_status = ''

        if os.stat(location_file).st_size <= 0:
            return ''

        with open(location_file) as my_file:
            for line in my_file:
                my_list = line.replace('\n', '').split(',')
                if i == 0 or my_list[0] == '':
                    i = 1
                    continue

                path_to_results_or_fail_msg = my_list[0]
                global_path = path_to_results_or_fail_msg[:path_to_results_or_fail_msg.find('run-time-info.xml')]
                test_name = my_list[1]
                test_protocol = my_list[2]
                date = str(my_list[3])
                time_run = str(my_list[4])
                if 'day' in time_run:
                    time_run += ',' + str(my_list[5])

                # if test ran didn't finish with 0 -> sign that run works -> don't check the results in file
                if "test failed during run" in path_to_results_or_fail_msg:
                    ReadEXCEL.update_test_status_in_excel(GlobalVariables.path_to_XL, test_name, "STOPPED", time_run,
                                                          global_path)

                    continue
                else:
                    if "stuck" in time_run:
                        # test didn't move from RunningRuns file to FinishedRuns file
                        old_status = time_run
                        time_run = GlobalFunctions.get_time_from_file(global_path)

                    item = ReadXML.read_xml_results(path_to_results_or_fail_msg, test_name,
                                                    test_protocol, date, time_run)

                    # taking numbers of success/ errors/ failures
                    num_passed = item[str_pass_casses]
                    num_failed = item[str_fail_casses]
                    num_other = item[str_other_casses]
                    num_remaining = item[str_remaining_casses]

                    if "stuck" in old_status:
                        ReadEXCEL.update_test_status_in_excel(GlobalVariables.path_to_XL, test_name, "STOPPED", time_run, global_path)

                    elif num_other == 0 and num_passed == 0 and num_failed == 0 \
                            or num_remaining != 0:
                        ReadEXCEL.update_test_status_in_excel(GlobalVariables.path_to_XL, test_name, "ERROR", time_run, global_path)

                    elif num_failed > 0:
                        ReadEXCEL.update_test_status_in_excel(GlobalVariables.path_to_XL, test_name, "finished FAIL", time_run, global_path)

                    elif num_other > 0:
                        ReadEXCEL.update_test_status_in_excel(GlobalVariables.path_to_XL, test_name, "finished PASS", time_run, global_path)

                    else:
                        ReadEXCEL.update_test_status_in_excel(GlobalVariables.path_to_XL, test_name, "finished PASS", time_run, global_path)

    except Exception as e:
        print(e.message)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print ("Please enter results directory that will update excel table.")
    else:
        GlobalFunctions.enable_logging('')
        update_XL_table(sys.argv[1] + '/ListOfFinishedRunsDetails.txt')
