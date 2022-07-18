from Queue import *
from threading import Lock

# Run module
# *Automatic* initialization of variable
num_ports = 0
logger = None
date = ''
start_time = ''
end_time = ''
current_time_of_run = ''
status_threads_list_for_reproducing = {}
path_to_lists_runs_details = ""
path_to_save_log = ''
path_to_save_server_log = ''

# *Configure* to any run (Regular or reproducingcd of failures)
LP_machine = '10.12.233.183'
DUT_machine = '10.12.232.122'
# which setup will send full cycle results- if don't have server put ***None***
server_machine = '10.12.233.183' # lizysha: new cycle for MH
dut_user = 'root'
dut_password = 'root00'
project = 'development'
path_to_recipients_file = '/root/PycharmProjects/DefensicsAutomation/FilesForAutomation/files/recipients1.txt'

# *Configure* for Regular run only! (not for Reproduce Failures or Publish Results)
path_to_XL = '/root/PycharmProjects/DefensicsAutomation/FilesForAutomation/files/LKV_part.xlsx'
path_to_testplans = '/net/ladj1734/home/svjer/defensics_logs/Automation_Test_plans/'
part_of_path_to_results = '/net/ladj1734/home/svjer/defensics_logs/Automation_Results/'
path_to_cycle_results = '/root/synopsys/defensics/Automation_Cycle_Results/'

path_to_cmds_files = '/root/PycharmProjects/DefensicsAutomation/FilesForAutomation/cmds/'
path_to_server_cmds_files = '/root/PycharmProjects/DefensicsAutomation/FilesForAutomation/server_cmds/'

# DefensicsAutomation module
# Counts
num_tests = 0
num_tests_to_reproduce = 0
num_finished_tests = 0
num_running_tests = 0

# Lists
ports_list = []
threads_queue = Queue()
threads_test_reproduce_queue = Queue()
running_threads_dic = {}
tests_queue = Queue()
list_results = []
status_devices_to_reproduce = {}
name_device_updated_in_status = {}

# Locks
first_threads_lock = Lock()
second_threads_lock = Lock()
third_threads_lock = Lock()
fourth_threads_lock = Lock()
excel_lock = Lock()
tests_lock = Lock()
tests_reproduce_lock = Lock()
status_device_reproduce_lock = Lock()
thread_reproduce_lock = Lock()
ssh_lock = Lock()
