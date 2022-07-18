#!/usr/bin/env python
import os
import time

activate_this = os.path.expanduser("~/PycharmProjects/DefensicsAutomation/venv/bin/activate_this.py")
execfile(activate_this, dict(__file__=activate_this))
import subprocess
import pexpect
import sys

# MH WA:
# device_to_machine = {'CVL0_0': '10.12.233.187',
#                      'CVL0_1': '10.12.233.117',
#                      'CVL0_2': '10.12.232.194',
#                      'CVL0_3': '10.12.232.185'
#                      }
DUT_machine = '10.12.232.122'
dut_user = 'root'
dut_password = 'root00'
path_to_files = '/root/PycharmProjects/DefensicsAutomation/FilesForAutomation/files/'
path_to_pcap_valid_packet_file = path_to_files + 'Valid_packet_defensics.pcap'


def ssh_copy_id(machine, user, password):
    str_ssh = '/usr/bin/ssh-copy-id  -i {} {}@{}'.format('/{}/.ssh/id_rsa.pub'.format(user), user, machine)
    child = pexpect.spawn(str_ssh)
    try:
        index = child.expect(['continue connecting \(yes/no\)',
                              '{}@{}\'s password:'.format(dut_user, machine), pexpect.EOF], timeout=20)
        print(str(index))

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
            print('[ key to {} exists ]'.format(machine))
            print(child.after, child.before)

        child.close()
    except pexpect.TIMEOUT:
        print(child.after, child.before)
        child.close()
    else:
        print('finished, ready')


def ssh_keygen(password):
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


def allow_ssh(machine):
    """
    This function will allow ssh to be automatic without password to DUT machine.
    (in order to run sever Defensics CMD)
    :param DUT_machine: name of DUT machine
    """
    try:
        user = dut_user
        password = dut_password
        subprocess.call('ssh-add', shell=True)
        subprocess.call('eval "$(ssh-agent -s)"', shell=True)

        ssh_keygen(password)
        ssh_copy_id(machine, user, password)

    except Exception as e:
        print(e.message)


def print_full_netstat_in_DUT(machine):
    cmd = 'ssh -t {} netstat -i'
    process = subprocess.call(cmd.format(machine), shell=True)


def check_interface_rx_by_netstat_in_DUT(intr):
    try:
        # lizysha MH WA
        machine = DUT_machine
        cmd = 'ssh -t {} netstat --interfaces={}'
        my_file = open(path_to_files + 'netstat_intr_results.txt', 'w')
        proccess = subprocess.call(cmd.format(machine, intr), stdout=my_file, shell=True, stderr=subprocess.STDOUT)
        my_file.close()

        my_file = open(path_to_files + 'netstat_intr_results.txt', 'r')
        lines = my_file.readlines()
        my_file.close()

        line_1 = 'empty'
        line_2 = 'empty'

        for line in lines:
            if line_1 == 'empty' and line.find("RX-OK") != -1:
                line_1 = line
                continue
            if line_1 is not 'empty':
                line_2 = line
                break

        list_1 = line_1.replace(' ', ',').split(',')
        list_2 = line_2.replace(' ', ',').split(',')

        new_list_1 = []
        new_list_2 = []

        for item in list_1:
            if item is not '':
                new_list_1.append(item)

        for item in list_2:
            if item is not '':
                new_list_2.append(item)

        if len(new_list_1) <= 2 and len(new_list_2) <= 2:
            print("ERROR - lists are empty. \nCheck if SSH work without password.\n"
                  "If not, there is problem with ssh_keygen function.")

        rx_ok = new_list_2[2]

        return rx_ok
    except Exception as e:
        print(e.message)


def send_valid_packet(intr, num):
    subprocess.call('tcpreplay --intf1={} --loop={} {}'.format(intr, num, path_to_pcap_valid_packet_file), shell=True)


def check_rx_changes(rx_ok_before, rx_ok_after, num_send):
    str_before = str(rx_ok_before)
    str_after = str(rx_ok_after)

    try:
        before = int(rx_ok_before)
        after = int(rx_ok_after)
    except:
        print("RX didn't succeeded - no value arrived\n")
        return 1

    num = int(num_send)

    if before == after:
        print("\nERROR: RX-OK doesn't change after valid packets were sent! - NOT as expected! "
              "(" + str_before + "->" + str_after + ")\n")
        return 1
    if before + num == after:
        print("\nOK: " + str(num_send) + " packets were added to RX-OK - as expected! "
                                       "(" + str_before + "->" + str_after + ")\n")
        return 0
    if after > before:
        print("\nWARNING: RX-OK counter is bigger after valid packets were sent - LLDP sent packets... "
              "(" + str_before + "->" + str_after + ")\n")
        return 0
    print("\nERROR: RX-OK counter is smaller after valid packets were sent -NOT as expected! "
          "(" + str_before + "->" + str_after + ")\n")
    return 1


def check_ping(ip, intr):
    # if this is IPv6
    if ':' in ip:
        response = os.system("ping6 -I {} -c 1 {} ".format(intr, ip))
    else:
        response = os.system("ping -c 1 " + ip)

    # and then check the response...
    if response == 0:
        pingstatus = "Network Active"
    else:
        pingstatus = "Network Error"

    return pingstatus


def check_device_status(intr, ip, num_send):
    # ping_status = check_ping(ip, intr)
    ping_status = "Network Error"

    if ping_status == "Network Error":
        print("Ping was Unreachable - starting to check RX TX of Packets....")
        rx_ok_before = check_interface_rx_by_netstat_in_DUT("mev_ts")
        print("RX-OK value from netstat *before* sending is: " + rx_ok_before + "\n")
        send_valid_packet("mev0_0", num_send)
        time.sleep(2)
        rx_ok_after = check_interface_rx_by_netstat_in_DUT("mev_ts")
        print("RX-OK value from netstat *after* sending is: " + rx_ok_after + "\n")
        result = check_rx_changes(rx_ok_before, rx_ok_after, num_send)
        exit(result)
    else:
        print("ping passed successfully")
        exit(0)


def check_device_status_for_external_use(intr, ip, num_send):
    ping_status = check_ping(ip, intr)

    if ping_status == "Network Error":
        rx_ok_before = check_interface_rx_by_netstat_in_DUT(intr)
        try:
            rx_ok_before = int(rx_ok_before)
        # if the convert to int will fail it's because
        except:
            print("RX didn't succeeded - no value arrived\n")
            print("==================================================")
            print("===ERROR - Valid packet did not arrive to DUT!!===")
            print("==================================================")
            return

        send_valid_packet(intr, num_send)
        rx_ok_after = check_interface_rx_by_netstat_in_DUT(intr)
        result = check_rx_changes(rx_ok_before, rx_ok_after, num_send)

        if result == 1:
            print("==================================================")
            print("===ERROR - Valid packet did not arrive to DUT!!===")
            print("==================================================")
        else:
            print("===================================================")
            print("====Valid packet arrived successfully to DUT :)====")
            print("===================================================")


if __name__ == '__main__':
    intr = 0
    ip = 0
    num_send = 0

    if len(sys.argv) < 3:
        print "Please enter ^interface^ and ^IP/IPv6^ and num of ^repeat^ you want to run the valid packet"
        exit()
    else:
        intr = sys.argv[1]
        # TODO to check lonly what is the IP!!!
        ip = sys.argv[2]
        num_send = sys.argv[3]

    # when have problems of ssh - unable the line
    # allow_ssh()

    check_device_status(intr, ip, num_send)

