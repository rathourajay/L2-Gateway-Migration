"""
Created on March 2016

@author: gur37673

Description: Neutron Credentials from neutron.conf

"""
import os
import codecs
import paramiko
import json
import config
import sys

        
class Neutron_Credentials:

    def __init__(self):
        self.host_ip = config.CONF.DATABASE_CRED.host_ip
        self.host_uname = config.CONF.DATABASE_CRED.host_uname
        self.host_pwd = config.CONF.DATABASE_CRED.host_pwd
        self.conf_file =  ''.join([os.getcwd(),'/conf/input_data.conf'])
        
    def fetch_credentials(self):
        '''
        Fetch neutron credentials from neutron.conf and \
        write to input_data.conf file
        [TO DO: Remove for loop and fix first time file refresh issue]
        '''
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.host_ip, username=self.host_uname, password=self.host_pwd)
        fetch_usr = "cat /etc/neutron/neutron.conf | grep '^admin_user = ' | awk '{print $NF}'"
        stdin, stdout, stderr  = client.exec_command(fetch_usr)
        for usr_item in stdout.readlines():
            pass
        fetch_passwd = "cat /etc/neutron/neutron.conf | grep '^admin_password = ' | awk '{print $NF}'"
        stdin, stdout, stderr  = client.exec_command(fetch_passwd)
        for pwd_item in stdout.readlines():
            pass
        with open(self.conf_file, 'r') as file: 
            data = file.readlines() 
            cnt = 0 
            for item in data:
                if item.startswith('db_user_id'): 
                    item = 'db_user_id = '
                    item += ''.join(usr_item)
                    data[cnt] = item
                    cnt += 1
                    continue 
                if item.startswith('db_pwd'):
                    item = 'db_pwd = '
                    item += ''.join(pwd_item)
                    data[cnt] = item 
                    break
                cnt += 1 
        
        with open(self.conf_file, 'w') as file: 
            file.writelines(data) 
            file.writelines('\n') 
    
    

