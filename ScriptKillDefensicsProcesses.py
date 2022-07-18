#!/usr/bin/env python
import os
activate_this = os.path.expanduser("~/PycharmProjects/DefensicsAutomation/venv/bin/activate_this.py")
execfile(activate_this, dict(__file__=activate_this))

import sys
import subprocess
import GlobalVariables


def kill_Defensics_processes():
    kill_line = "ps -aux | grep java | grep testplan | tr -s ' ' | cut -d ' ' -f 2  |  xargs kill -9"
    try:
        subprocess.call(kill_line, shell=True, stderr=subprocess.PIPE)
    except Exception as e:
        print("ERROR occurred when tried to kill Defensics processes! " + e.message)
        return

    print("All **local** Defensics processes where killed successfully :)")


def kill_remote_Defensics_processes():
    kill_line = 'ssh {}  "pid=\$(ps -aux | grep java | grep testplan | tr -s \' \' | cut -d \' \' -f 2 ); ' \
                'echo \$pid | xargs kill -9"'
    try:
        subprocess.call(kill_line.format(GlobalVariables.DUT_machine), shell=True, stderr=subprocess.PIPE)

    except Exception as e:
        print("ERROR occurred when tried to kill Defensics processes! " + e.message)
        return

    print("All **remote** Defensics processes where killed successfully :)")

if __name__ == '__main__':
    kill_remote = 0

    if len(sys.argv) < 2:
        print ("Please enter 1 if you want to kill also remote processes, 0 otherwise")
        exit()
    else:
        kill_remote = int(sys.argv[1])

    kill_Defensics_processes()

    if kill_remote == 1:
        kill_remote_Defensics_processes()


