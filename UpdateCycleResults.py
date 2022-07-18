#!/usr/bin/env python
import os
activate_this = os.path.expanduser("~/PycharmProjects/DefensicsAutomation/venv/bin/activate_this.py")
execfile(activate_this, dict(__file__=activate_this))

import SendDailyCycleResults
import GlobalFunctions


if __name__ == '__main__':
    print ("Updating Cycle Results......")
    GlobalFunctions.enable_logging('')
    SendDailyCycleResults.copy_XL_from_remote_running_setups()
    SendDailyCycleResults.update_protocols_XLs_locally()
    print ("in server update......")
