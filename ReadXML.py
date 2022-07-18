import xml.etree.ElementTree as ET
import os


def read_xml_results(location, test_name, protocol, date, time_run):
    try:
        dic_results = {'name test': test_name, 'protocol': protocol, 'date': date,
                       'state': '',
                       'passed-cases': 0, 'failed-cases': 0, 'other-cases': 0, 'remaining-cases': 0,
                       'run-time': '00:00:00'}

        if not os.path.exists(location):
            dic_results['state'] = "stuck!! location doesn't exist."
            return dic_results
        elif "run-time-info.xml" not in location:
            dic_results['state'] = "stuck!! file isn't 'run-time-info.xml' file."
            return dic_results
        elif os.stat(location).st_size == 0:
            dic_results['state'] = "stuck!! file 'run-time-info.xml' is empty."
            return dic_results
        else:
            tree = ET.parse(location)
            root = tree.getroot()
            state = root.find('state').text
            passed_cases = int(root.find('passed-cases').text)
            failed_cases = sum_fail_tags(location)
            other_cases = int(root.find('other-cases').text)
            remaining_cases = int(root.find('remaining-cases').text)
            dic_results = {'name test': test_name, 'protocol': protocol, 'date': date, 'state': state,
                           'passed-cases': passed_cases, 'failed-cases': failed_cases,'other-cases': other_cases,
                           'remaining-cases': remaining_cases, 'run-time': time_run}

        return dic_results
    except Exception as e:
        # TODO log?
        print(e.message)


# TODO those tags need to be mention as fail?
def sum_fail_tags(location):
    try:
        tree = ET.parse(location)
        root = tree.getroot()
        sum_fail = int(root.find('failed-cases').text)
        sum_fail += int(root.find('failed-snmp-cases').text)
        sum_fail += int(root.find('failed-snmp-traps').text)
        # sum_fail += int(root.find('failed-safe-guard-checks').text)
        sum_fail += int(root.find('failed-isa-secure-cases').text)
        sum_fail += int(root.find('failed-syslog-messages').text)
        return sum_fail
    except Exception as e:
        print(e.message)
