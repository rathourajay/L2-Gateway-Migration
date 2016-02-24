"""
Created on Feb 2016

@author: 

Description: Migration Script

"""

import requests
import json
import csv
import os
import sys
from common import exceptions
from common import config_reader
from common import request
from common import config
from common import database_connection
import logging
import webob.exc
from common.exceptions import UnhandeledException
import re

ADMIN_DIR = ''
USER_DIR = ''
CONF_FILE = "/home/ubuntu/L2-Gateway-Migration/conf/input_data.conf"
DATA_FILE = "/home/ubuntu/L2-Gateway-Migration/data/"

class MigrationScript(object):

    def __init__(self):
        global USER_DIR
        global ADMIN_DIR
        self.cfile = os.getcwd()
        USER_DIR = self.cfile + '/../data/'
        #ADMIN_DIR = self.cfile + '/../conf/admin'
        log_level = logging.INFO
        if config.CONF.default.debug:
            log_level = logging.DEBUG
        self.init_log(config.CONF.OPENSTACK_CREDS.log_file, log_level, 'l2_gateway')
        self.log = logging.getLogger('l2_gateway')


    def init_log(self, filename, level, logger):
        
        directory = os.path.dirname(filename)
        if not os.path.exists(directory):
            os.makedirs(directory)
        l = logging.getLogger(logger)
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s - %(message)s')
        fileHandler = logging.FileHandler(filename, mode='a')
        fileHandler.setFormatter(formatter)
        l.setLevel(level)
        l.addHandler(fileHandler)

    
    def get_headers(self):      
        """
        Fetch headers to create token
        """ 
        
        creds_dict = config_reader.get_config_vals(CONF_FILE)
        cred_list = creds_dict['cred_list']
        """To Do: Make a generic method"""
        self.log.info("In Function get_headers")
        username = cred_list[0][1]
        password = cred_list[1][1]
        tenant_name = cred_list[2][1]
        auth_token = request.get_user_token(username,password,tenant_name,CONF_FILE)

        token_id = auth_token['token']['id']
        headers = {
                'User-Agent': 'python-neutronclient',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Auth-Token': token_id,
                }
        self.log.info("Token Retrieved with value: %s" % (token_id))
        return headers


    def populate_data_file(self,connection_list):
        """
        Populating csv data file
        """
        try:
            self.log.debug("Populating csv file for connection list")
            data_file = DATA_FILE + 'data_file.csv'
            with open(data_file, 'wb') as fp:
                writer = csv.writer(fp, delimiter='\t')
                connection_dict = json.loads(connection_list.encode('utf-8'))
                writer.writerow(["connection_id", "network_id", "tenant_id", "l2_gateway_id", "segmentation_id"])
                for conn_lists in connection_dict.itervalues():
                    for item in range(len(conn_lists)):
                        connection_id = connection_dict["l2_gateway_connections"][item]["id"]
                        network_id = connection_dict["l2_gateway_connections"][item]["network_id"]
                        tenant_id =  connection_dict["l2_gateway_connections"][item]["tenant_id"]
                        l2_gateway_id = connection_dict["l2_gateway_connections"][item]["l2_gateway_id"]
                        segmentation_id = connection_dict["l2_gateway_connections"][item]["segmentation_id"]
                        writer.writerow([connection_id, network_id, tenant_id, l2_gateway_id, segmentation_id])
            self.log.info("CSV file generated for connection list")
        except IOError:
            print "Error in writing csv file:", data_file


    def read_data_file(self):
        """
        Read contents from data file
        """
        try:
            data_file = DATA_FILE + 'data_file.csv'
            with open(data_file, 'rb') as fp:
                reader = csv.reader(fp, delimiter='\t')
                count = 0
                param_dict = {}
                conn_id_list = []
                net_id_list = []
                gw_id_list = []
                for row in reader:
                    if count == 0:
                        count = count + 1
                    else:
                        conn_id_list.append(row[0])
                        net_id_list.append(row[1])
                        gw_id_list.append(row[3])
                """
                TO DO: Apply validation over param_dict
                """ 
                param_dict['connection_id'] = conn_id_list
                param_dict['net_id']=net_id_list
                param_dict['gw_id']=gw_id_list
        
        except IOError:
            print "Error in reading csv file:", data_file
 
        self.log.info("Content extracted freom data file %s" % (param_dict))
        return param_dict


    def update_l2gwagent_ini(self):
        with open('l2gw-agent1.ini', 'r') as file:
            """
            TODO give correct path of l2gwini file,list ips should be read from conf file, validation check on ip
            """
            list_ips = ['ovsdb1:16.95.16.1:6632,ovsdb2:16.95.16.2:6632','ovsdb1:16.95.16.1.22:8989']
            self.log.info("Updating INI file corresponding to IPS =  %s" % (list_ips))
            data = file.readlines()
            cnt = 0
            for item in data:
                parm_pat = re.findall(r'\#\s*ovsdb_hosts.\s*\=\s*',item,re.DOTALL)
                if item.startswith('ovsdb_hosts') or parm_pat:
                    item = 'ovsdb_hosts ='
                    item +=','.join(list_ips).replace('\#', '')
                    break
                cnt += 1
        item = item+'\n'
        data[cnt] = item
        with open('l2gw-agent1.ini', 'w') as file:
            file.writelines( data )
            file.writelines('\n')
        self.log.info("##INI file updated## ")


    def create_connection(self,param_dict,req_url,headers):
        for i in range(len(param_dict['net_id'])):
            network_id = param_dict['net_id'][i]
            l2_gateway_id = param_dict['gw_id'][i]
            payload = {"l2_gateway_connection": {"network_id": network_id, "l2_gateway_id": l2_gateway_id}}
            """
            creating connection
            """
            create_conn = requests.post(req_url, data=json.dumps(payload), headers=headers)
            
            self.log.info("Creating connection with command %s" %(create_conn.text))
            self.log.info("connection created")


    def get_connections_list(self,req_url,headers):
        """
        Fetching connection list available on source
        """
        list_conn = requests.get(req_url, headers=headers)
        connection_list = list_conn.text

        self.log.debug("Fetched connection List: %s" % (connection_list))
        return connection_list



    def execute_migration(self):
        
	"""
        Executing L2GW migration steps
        """
        self.log.info("Executing Migration")
        self.log.info("Fetching Connection list")
        creds_dict = config_reader.get_config_vals(CONF_FILE)
        controller_ip = creds_dict['controller_ip']
        req_url = "http://%s:9696/v2.0/l2-gateway-connections.json"  % (controller_ip)
        headers = self.get_headers()
        
        try:
            sys.stdout.write("1. Fetching Connection List\n")
            connection_list = self.get_connections_list(req_url,headers)
            self.log.info("Connection list %s" % (connection_list))
            
            sys.stdout.write("2. Populating data file\n")
            self.populate_data_file(connection_list)
            self.log.info("##Datafile populated##")

            sys.stdout.write("3. Deleting Entry from MySql\n")
            db_obj = database_connection.db_connection()
            self.log.info("##Connected to database##")
            db_obj.read_connection_uuid()
            self.log.info("##Deleting connection data from database##")
            
            self.log.info("##Creating Connection on destination##")
            sys.stdout.write("4. Creating Connection\n")
            param_dict = self.read_data_file()
            self.create_connection(param_dict,req_url,headers=headers)        
            self.log.info("##Connection created on destination##")
            sys.stdout.write("5. Connection created successfully\n")
            #self.update_l2gwagent_ini()
        
        except (requests.exceptions.HTTPError) as e:
            print "An HTTPError:", e.message
        except webob.exc.HTTPError() as e:
            raise webob.exc.HTTPError(e)
        except Exception as e:
            raise UnhandeledException(e)
        
