import GlobalVariables
import os


class MyTestPlan:
    def __init__(self, protocol, name, giga, is_server_needed_client=False, is_reproduce=False, log_dir=False):
        self.testplan_line = ''
        self.protocol = protocol
        self.name = name
        self.giga_for_test = giga
        self.is_server_needed_client = is_server_needed_client
        self.is_reproduce = is_reproduce
        # self.server_log_dir = '/root/server_results/'
        self.log_dir = self.path_to_log_dir(log_dir)
        self.cmd = ''
        self.server_cmd = ''
        self.cmd_from_file()

    def print_data(self):
        """
        print testplans details

        """
        GlobalVariables.logger.info("name test: " + self.name)
        GlobalVariables.logger.info("protocol: " + self.protocol)
        GlobalVariables.logger.info("giga: " + self.giga_for_test)
        GlobalVariables.logger.info("\ncmd: " + self.cmd)
        if self.is_server_needed_client is True:
            GlobalVariables.logger.info("\nserver side cmd: " + self.server_cmd)

    def cmd_from_file(self):
        """
        This function take from files the cmd of current testplan
        and fill the variable self.cmd with the value
        """
        try:
            if self.is_reproduce is False:
                # if the path doesn't exist(for example this is a reproducing of test) - exit
                if not os.path.exists(GlobalVariables.path_to_cmds_files + self.protocol + '/' + self.name + '.txt'):
                    # TODO why we can't create the directory and file right now?? what's the problem
                    GlobalVariables.logger.error('ERROR: there is no path to: ' + GlobalVariables.path_to_cmds_files + self.protocol
                          + '/' + self.name + '.txt')
                    exit()

                f = open(GlobalVariables.path_to_cmds_files + self.protocol + '/' + self.name + '.txt', 'r')
                self.cmd = f.read().replace('\n', '')
                f.close()

                # if this test need to run with server side
                if self.is_server_needed_client is True:
                    server_test_name = self.name.replace('Client', 'Server')
                    server_protocol = self.protocol.replace('Client', 'Server')

                    f = open(GlobalVariables.path_to_server_cmds_files + server_protocol + '/' +
                             server_test_name + '_For_Client.txt', 'r')
                    self.server_cmd = f.read().replace('\n', '')

                    # save lone of java -jar + testplan, the will be able to stop it if the run is client/server
                    self.testplan_line = self.server_cmd[:self.server_cmd.find('.testplan')]

                f.close()
        except Exception as e:
            GlobalVariables.logger.error(e.message)

    def path_to_log_dir(self, log_to_reproduce):
        """
        This create log directory for the current testplan.
        :return: log directory for current testplan.

        """
        try:

            # if i don't get log_dir, it mean we are in REGULAR run.
            # otherwise it means we are in REPRODUCING run
            if self.is_reproduce is False:

                if not os.path.exists(GlobalVariables.part_of_path_to_results + '/' + GlobalVariables.date + '_' +
                                      GlobalVariables.project + '/' + self.protocol):
                    os.makedirs(GlobalVariables.part_of_path_to_results + '/' + GlobalVariables.date + '_' +
                                GlobalVariables.project + '/' + self.protocol)

                os.makedirs(GlobalVariables.part_of_path_to_results + '/' + GlobalVariables.date + '_' +
                            GlobalVariables.project + '/' + self.protocol + '/' + self.name)
                log_dir = GlobalVariables.part_of_path_to_results + GlobalVariables.date + '_' + GlobalVariables.project \
                          + '/' + self.protocol + '/' + self.name + '/'
            else:
                log_dir = log_to_reproduce

            # create a file that will show start/end and current run time of a test
            time_file = open(log_dir + '/RunTime.txt', 'w+')
            time_file.close()

            return log_dir
        except Exception as e:
            GlobalVariables.logger.error(e.message)
