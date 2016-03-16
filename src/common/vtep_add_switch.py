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
        self.cmc_ip = '10.8.20.51'
        self.cc1_ip = '10.8.20.52'
        self.cc2_ip = '10.8.20.53'
        self.switch_data = os.getcwd()+ '/../../data/' + 'switch_data.csv'

    def connect_host(self,switch_ip,switch_username,switch_password):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(switch_ip, username=switch_username, password=switch_password)
        log.info("Connecting to Switch with ip %s " % (switch_ip))
#        import pdb;pdb.set_trace()
#        ps = client.exec_command('sudo ./vtep-ctl list-ps')
        

        return client

    def execute_vtep_cmd(self,client):
        #query = 'sudo mysql -e "delete from l2gatewayconnections where id = \'%s\'" -u %s -p%s %s' % (uuid_con,self.db_user_id,self.db_pwd,self.db_name) 
        #import pdb;pdb.set_trace()
        command_vtep = "cd /home/ubuntu;./vtep-ctl list Physical_Port"
#        command_vtep = "cd /home/ubuntu;./vtep-ctl set-manager \'tcp:%s:6632\'" % (self.cmc_ip) 
        #command_vtep = "sudo ./vtep-ctl set-manager \'tcp:%s:6632\'" % (self.cmc_ip) 
        stdin, stdout, stderr = client.exec_command(command_vtep)
        log.info("Setting ip in VTEP manager for CMC with ip  %s " %(self.cmc_ip))
        command_vtep = 'cd /home/ubuntu;./vtep-ctl set-manager \'tcp:%s:6632\'' % (self.cc1_ip) 
        stdin, stdout, stderr = client.exec_command(command_vtep)
        log.info("Setting ip in VTEP manager for CMC with ip  %s " %(self.cc1_ip))
        command_vtep = 'cd /home/ubuntu;./vtep-ctl set-manager \'tcp:%s:6632\'' % (self.cc2_ip) 
        stdin, stdout, stderr = client.exec_command(command_vtep)
        log.info("Setting ip in VTEP manager for CMC with ip  %s " %(self.cc2_ip))
        for line in stdout:
            print line.strip('\n')


    def csv_for_switch_details(self):
        self.log.info("Populate csv file for switch detail input")
        #data_file = self.CSV_PATH + '/../../data/'
        #switch_data = data_file + 'switch_dat.csv'
        sys.stdout.write("Please provide switch details to %s" %(self.switch_data))
        with open(self.switch_data, 'wb') as fp:
            writer = csv.writer(fp, delimiter='\t')
            writer.writerow(["switch_name", "switch_ip", "switch_username", "switch_password"])

    def read_execute_switch_data(self):
        #data_file = self.CSV_PATH + '/../../data/'
        #switch_data = data_file + 'switch_dat.csv'
        log.info("Reading switch details")
        switch_ptr = self.connect_host('10.8.20.112','root','ubuntu')
        self.execute_vtep_cmd(switch_ptr)
        '''
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
            sys.stderr.write('ERROR in reading file.....\n')
        '''
    
    def get_ovsdb_bindings(self):
        '''
        This method retruns vlan_bindings wrt port name
        '''
        client = self.connect_host('10.8.20.112','root','ubuntu')
        command_vtep = "cd /home/ubuntu;./vtep-ctl list Physical_Port"
	command_vtep_switches = "cd /home/ubuntu;./vtep-ctl list Physical_Switch"
        stdin, stdout, stderr = client.exec_command(command_vtep)
        name_list = []
	port_id_list = []
        binding_list = []
        for item in stdout.readlines():
	    if '_uuid' in item:
	        port_id_list.append(item)
            if 'name' in item:
                name_list.append(item)
            if 'binding' in item:
                binding_list.append(item)
        
        list_dicts = []
        for name,bindings,port_id in zip(name_list,binding_list,port_id_list):
            dict_name = {}
            dict_name['name'] = name
            dict_name['bindings'] = bindings
	    dict_name['port_id'] = port_id
            list_dicts.append(dict_name)

        stdin, stdout, stderr = client.exec_command(command_vtep_switches)
	port_list = []
	sw_name_list = []
	switch_details = {}
        
	for i in stdout.readlines():
            switch_details = dict()
            if 'name' in i:
                sw_name_list.append(i)
	    if 'ports' in i:
	        port_list.append(i)
        sw_detail_list  = []
	for name,port in zip(sw_name_list,port_list):
            sw_dict = {}
            sw_dict['sw_name'] = name
            sw_dict['ports'] = port
            sw_detail_list.append(sw_dict)
        return list_dicts,sw_detail_list
"""
if __name__=='__main__':
    adi = vtep_command_manager()
    adi.read_execute_switch_data() 
"""
