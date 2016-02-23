import codecs
import csv
import paramiko
import json
import config
import logging
import exceptions
import sys

log = logging.getLogger('l2_gateway')
PATH ='/home/ubuntu/L2-Gateway-Migration/data/'
class db_connection():

    def __init__(self):
        self.host_ip = config.CONF.DATABASE_CRED.host_ip
        self.host_uname = config.CONF.DATABASE_CRED.host_uname
        self.host_pwd = config.CONF.DATABASE_CRED.host_pwd
        self.db_user_id = config.CONF.DATABASE_CRED.db_user_id
        self.db_pwd = config.CONF.DATABASE_CRED.db_pwd
        self.db_name = config.CONF.DATABASE_CRED.db_name

    def connect_host(self):
        try:
	    client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.host_ip, username=self.host_uname, password=self.host_pwd)
            log.info("Connecting to host with ip %s " % (self.host_ip))
        except MySQLdb.Error as ex:
            self.log.exception("Could not connect to mysql host: %s. "
                               "Reason: %s" % (self.host_ip, ex))
            sys.stdout.write(_("Could not connect to mysql host: %s. "
                               "Reason: %s\n") % (self.host_ip, ex))
            raise exceptions.DBError(ex)
        return client

    def read_connection_uuid(self):
        data_file = PATH + 'data_file.csv' 
        con_ptr = self.connect_host()
        log.info("Reading connection UUID from CSV file to be deleted")
        arr = []
        try:
            with open(data_file, 'r') as fd:
                reader =  csv.reader(fd, delimiter='\t')
                for line in reader:
                    arr.append(line[0])
            
            for item in arr[1:]:
                log.info("Connection UUID to be deleted from database  %s " %(item))
                self.execute_query(con_ptr,item)
        except exceptions.InputOutput as message:
            raise exceptions.InputOutput('unable to read file')
            sys.stdout.write('ERROR in reading file.....\n')

    def execute_query(self,client,uuid_con):
        #import pdb;pdb.set_trace()
        #query = 'sudo mysql -e "select * from l2gatewayconnections" -u neutron -p7342274ae48f99a6262b3653496a02ccb9398d07 ovs_neutron'
        query = 'sudo mysql -e "delete from l2gatewayconnections where id = \'%s\'" -u %s -p%s %s' % (uuid_con,self.db_user_id,self.db_pwd,self.db_name)
        log.info("Query for deleting the data from l2gatewayconnections table  %s " %(query))
        try:
            stdin, stdout, stderr = client.exec_command(query)
            for line in stdout:
                print line.strip('\n')
        except MySQLdb.Error as ex:
            self.log.exception("Could not connect to mysql and query fails to execute: %s. "
                               "Reason: %s" % (self.host_ip, ex))
            sys.stdout.write(_("Could not connect to mysql host: %s. "
                               "Reason: %s\n") % (self.host_ip, ex))
            raise exceptions.DBError(ex)
