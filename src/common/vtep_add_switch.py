import codecs
import csv
import paramiko
import json
import config
import logging

log = logging.getLogger('l2_gateway')
PATH ='/home/ubuntu/L2-Gateway-Migration/data/'
class vtep_command_manager():

    def __init__(self):
        #self.host_ip = config.CONF.DATABASE_CRED.host_ip
        self.cmc_ip = config.CONF.DATABASE_CRED.host_uname
        self.cc1_ip = config.CONF.DATABASE_CRED.host_pwd
        self.cc2_ip = config.CONF.DATABASE_CRED.db_user_id
        self.db_pwd = config.CONF.DATABASE_CRED.db_pwd
        self.db_name = config.CONF.DATABASE_CRED.db_name

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

    def connect_execute_cmd(self)
        #Read data from file 
        #connect to particular switch (iterate the list) eg: connect_ret=connect_host('10.8.20.1','switch1','switch_pwd')
        # Execute the vtep cmd eg: execute_vtep_cmd(connect_ret)

    
