#!/usr/bin/env python
import os
activate_this = os.path.expanduser("~/PycharmProjects/DefensicsAutomation/venv/bin/activate_this.py")
execfile(activate_this, dict(__file__=activate_this))
import CheckAndSendResults
import sys


def send_email(path_to_list_results, txt):
    CheckAndSendResults.send_results(path_to_list_results, txt)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print ("Please enter results directory")
    else:
        # TODO add output file
        additional_txt_tittle = "Publish Results"
        send_email(sys.argv[1], additional_txt_tittle)
