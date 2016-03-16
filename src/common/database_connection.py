"""
Created on Feb 2016

@author: gur40998

Description: Datbase operations for L2 Migration

"""
import codecs
import csv
import paramiko
import json
import config
import logging
import migration_exceptions
import sys
import os
log = logging.getLogger('l2_gateway')
class db_connection():

    def __init__(self):
        self.host_ip = config.CONF.DATABASE_CRED.host_ip
        self.host_uname = config.CONF.DATABASE_CRED.host_uname
        self.host_pwd = config.CONF.DATABASE_CRED.host_pwd
        self.db_user_id = config.CONF.DATABASE_CRED.db_user_id
        self.db_pwd = config.CONF.DATABASE_CRED.db_pwd
        self.db_name = config.CONF.DATABASE_CRED.db_name
#        import pdb;pdb.set_trace()

    def connect_host(self):
        try:
	    client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.host_ip, username=self.host_uname, password=self.host_pwd)
            log.info("Connecting to host with ip %s " % (self.host_ip))
        except MySQLdb.Error as ex:
            self.log.exception("Could not connect to mysql host: %s. "
                               "Reason: %s" % (self.host_ip, ex))
            sys.stderr.write("Could not connect to mysql host: %s. "
                               "Reason: %s\n" % (self.host_ip, ex))
            raise migration_exceptions.DBError(ex)
        except Exception as e:
             self.log.exception('ERROR in connecting to MYSQL\n')
        return client

    def read_connection_uuid(self):
        data_file = os.getcwd() + '/data/data_file.csv' 
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
                self.delete_connection(con_ptr,item)
        except migration_exceptions.InputOutput as message:
            sys.stderr.write('ERROR in reading file.....\n')
            self.log.exception('ERROR in reading file.....\n')
            raise migration_exceptions.InputOutput('unable to read file')

    def delete_connection(self,client,uuid_con):
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
            sys.stderr.write("Could not connect to mysql host: %s. "
                               "Reason: %s\n" % (self.host_ip, ex))
            raise migration_exceptions.DBError(ex)
        except Exception as e:
             self.log.exception('Error in executing \n')
