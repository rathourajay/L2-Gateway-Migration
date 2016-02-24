import codecs
import csv
import paramiko
import json
import config
import logging
import os

log = logging.getLogger('l2_gateway')
class vtep_command_manager():

    def __init__(self):
        #self.host_ip = config.CONF.DATABASE_CRED.host_ip
        self.cmc_ip = config.CONF.DATABASE_CRED.host_uname
        self.cc1_ip = config.CONF.DATABASE_CRED.host_pwd
        self.cc2_ip = config.CONF.DATABASE_CRED.db_user_id
        CSV_PATH = os.getcwd() 

    def connect_host(self,switch_ip,switch_username,switch_password):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(switch_ip, username=switch_username, password=switch_password)
        log.info("Connecting to Switch with ip %s " % (switch_ip))
        return client

    def execute_vtep_cmd(self,client):
        #query = 'sudo mysql -e "delete from l2gatewayconnections where id = \'%s\'" -u %s -p%s %s' % (uuid_con,self.db_user_id,self.db_pwd,self.db_name) 
        command_vtep = 'sudo vtep-ctl set-manager\'tcp:%s:6632\'' % (self.cmc_ip) 
        stdin, stdout, stderr = client.exec_command(query)
        log.info("Setting ip in VTEP manager for CMC with ip  %s " %(self.cmc_ip))
        command_vtep = 'sudo vtep-ctl set-manager\'tcp:%s:6632\'' % (self.cc1_ip) 
        stdin, stdout, stderr = client.exec_command(query)
        log.info("Setting ip in VTEP manager for CMC with ip  %s " %(self.cc1_ip))
        command_vtep = 'sudo vtep-ctl set-manager\'tcp:%s:6632\'' % (self.cc2_ip) 
        stdin, stdout, stderr = client.exec_command(query)
        log.info("Setting ip in VTEP manager for CMC with ip  %s " %(self.cc2_ip))
        for line in stdout:
            print line.strip('\n')


    def csv_for_switch_details(self):
        self.log.info("Populate csv file for switch detail input")
        data_file = CSV_PATH + '/../../data/'
        switch_data = data_file + 'switch_dat.csv'
        sys.stdout.write("Please provide switch details to %s" %(switch_data))
        with open(switch_data, 'wb') as fp:
            writer = csv.writer(fp, delimiter='\t')
            writer.writerow(["switch_name", "switch_ip", "switch_username", "switch_password"])

   def read_ececute_switch_data(self)
        data_file = CSV_PATH + '/../../data/'
        switch_data = data_file + 'switch_dat.csv'
        log.info("Reading switch details")
        try:
            with open(data_file, 'r') as fd:
                reader =  csv.reader(fd, delimiter='\t')
                count = 0
                for row in reader:
                    if count == 0:
                        count = count + 1
                    else:
                       switch_ptr = connect_host(row[1],row[2],row[3]) 
                       execute_vtep_cmd(switch_ptr)
        except exceptions.InputOutput as message:
            raise exceptions.InputOutput('unable to read file')
            sys.stdout.write('ERROR in reading file.....\n')

