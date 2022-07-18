#!/usr/bin/env python
import os
activate_this = os.path.expanduser("~/PycharmProjects/DefensicsAutomation/venv/bin/activate_this.py")
execfile(activate_this, dict(__file__=activate_this))

import GlobalFunctions
import GlobalVariables
import subprocess
import sys
import Run


def get_list_physical_address_for_PCIe_devices():
    l_pcie_address = []

    for port in GlobalVariables.ports_list:
        cmd = 'ssh {0} "ethtool -i {1}"'.format(GlobalVariables.DUT_machine, port.device_name)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=None, shell=True)
        result = p.communicate()[0]
        result = result[result.find('info: '):]
        pcie = result[6:result.find('.')]

        if pcie not in l_pcie_address:
            l_pcie_address.append(pcie)

    return l_pcie_address


def run_flow_reset(type_reset):
    num_boards = 0

    l_pcie_address = get_list_physical_address_for_PCIe_devices()
    reset_cmd = "ssh {0} 'cd /sys/kernel/debug/ice/{1}; echo {2} > command'"

    for pcie in l_pcie_address:
        num_boards += 1
        pcie_str = pcie.replace(':', '\:') + '.0'
        reset_cmd = reset_cmd.format(GlobalVariables.DUT_machine, pcie_str, type_reset)
        try:
            p = subprocess.Popen(reset_cmd, stdout=subprocess.PIPE, stderr=None, shell=True)
            print('====Reset occurred :)==== (board ' + str(num_boards) + ' - ' + pcie + ')')
        except Exception as e:
            print('ERROR occurred during Reset.\n' + e.message)


if __name__ == '__main__':
    type_reset = ''
    if len(sys.argv) < 2:
        print "Please enter type of Reset (globr/corer)"
        exit()
    else:
        type_reset = sys.argv[1]

    print('Attempting to do Reset.....')
    # allow ssh to DUT machine
    # GlobalFunctions.allow_ssh()
    Run.add_ports()
    run_flow_reset(type_reset)
