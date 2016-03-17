"""
Created on Feb 2016

@author: 

Description: Migration Script

"""
import socket
import requests
import json
import csv
import os
import sys
from common import migration_exceptions
from common import token_generator
from common import config
from common import database_connection
import logging
import webob.exc
from common.migration_exceptions import UnhandeledException
import re
from common.vtep_add_switch import vtep_command_manager
from common.neutron_creds import Neutron_Credentials
import time

class MigrationScript(object):

    def __init__(self):
        
        self.DATA_FILE = ''.join([''.join([os.getcwd(),'/data/']), 'data_file.csv'])
        self.DATA_EXC_FILE = ''.join([''.join([os.getcwd(),'/data/']), 'failed_switches.csv'])
        self.host_ip = config.CONF.DATABASE_CRED.host_ip
        self.username = config.CONF.KEYSTONE_CREDS.username
        self.password =  config.CONF.KEYSTONE_CREDS.password
        self.tenant_name =  config.CONF.KEYSTONE_CREDS.tenant_name
        self.logfile = os.getcwd() + config.CONF.KEYSTONE_CREDS.log_file
        log_level = logging.INFO
        if config.CONF.default.debug:
            log_level = logging.DEBUG
        self.init_log(self.logfile, log_level, 'l2_gateway')
        self.log = logging.getLogger('l2_gateway')
        self.bind_obj = vtep_command_manager()
        self.neutron_obj = Neutron_Credentials()

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
        
        self.log.info("In Function get_headers")
        auth_token = token_generator.get_user_token(self.username,self.password,self.tenant_name,self.host_ip)

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
            with open(self.DATA_FILE, 'wb') as fp:
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
        except IOError as ex:
            sys.stdout.write("Error in writing csv file:", data_file)
            self.log.debug("Error in writing csv file: %s" %(data_file))
            self.log.exception("Error in writing csv file: %s. "
                               "Reason: %s" % (data_file, ex))
            sys.stderr.write(_("Error in writing csv file: %s. "
                               "Reason: %s\n") % (data_file, ex))


    def read_data_file(self, conn_file):
        """
        Read contents from data file
        """
        try:
            with open(conn_file, 'rb') as fp:
                reader = csv.reader(fp, delimiter='\t')
                count = 0
                param_dict = {}
                conn_id_list = []
                net_id_list = []
                tennt_id_list = []
                gw_id_list = []
                seg_id_list = []
                for row in reader:
                    if count == 0:
                        count = count + 1
                    else:
                        conn_id_list.append(row[0])
                        net_id_list.append(row[1])
                        tennt_id_list.append(row[2])
                        gw_id_list.append(row[3])
                        seg_id_list.append(row[4])
                """
                TO DO: Apply validation over param_dict
                """ 
                param_dict['connection_id'] = conn_id_list
                param_dict['net_id']=net_id_list
                param_dict['tennt_id']=tennt_id_list
                param_dict['gw_id']=gw_id_list
                param_dict['seg_id']=seg_id_list
        
        except IOError:
            sys.stdout.write("Error in reading csv file:", conn_file)
            self.log.debug("Error in reading csv file: %s" %(data_file))
            self.log.exception("Error in reading csv file: %s. "
                               "Reason: %s" % (conn_file, ex))
            sys.stderr.write(_("Error in reading csv file: %s. "
                               "Reason: %s\n") % (conn_file, ex))
 
        self.log.info("Content extracted from data file %s" % (param_dict))
        return param_dict


    def create_failure_file(self,connectn_id, network_id , tenant_id, seg_id, l2_gateway_id):
        failure_file = self.DATA_EXC_FILE
        try: 
            with open(failure_file, 'a') as fep:
                writer1 = csv.writer(fep, delimiter='\t')
                writer1.writerow(["connection_id", "network_id", "tenant_id", "l2_gateway_id", "segmentation_id"])
                writer1.writerow([connectn_id, network_id, tenant_id, l2_gateway_id, seg_id])
        except IOError as ex:
            print "Error in writing failure file:", data_file
            self.log.debug("Error in writing failure file: %s" %(data_file))
            self.log.exception("Error in writing csv file: %s. "
                               "Reason: %s" % (data_file, ex))
            sys.stderr.write(_("Error in writing csv file: %s. "
                               "Reason: %s\n") % (data_file, ex))



    def delete_csv_entries(self,to_del_param):
        failure_file = self.DATA_EXC_FILE
        try: 
            with open(failure_file, 'w') as fp:
                writer1 = csv.writer(fp, delimiter='\t')
                writer1.writerow(["connection_id", "network_id", "tenant_id", "l2_gateway_id", "segmentation_id"])
                for each_dict in to_del_param:
		    net_id = each_dict['network_id']
                    tenant_id = each_dict['tenant_id']
    		    conn_id = each_dict['connectn_id']
    		    gw_id = each_dict['l2_gateway_id']
	            seg_id = each_dict['seg_id']
                    writer1.writerow([conn_id, net_id, tenant_id, gw_id, seg_id])
        except IOError as ex:
            print "Error in writing failure file:", data_file
            self.log.debug("Error in writing failure file: %s" %(data_file))
            self.log.exception("Error in writing csv file: %s. "
                               "Reason: %s" % (data_file, ex))
            sys.stderr.write(("Error in writing csv file: %s. "
                               "Reason: %s\n") % (data_file, ex))



    def create_failed_connection(self,param_dict,req_url,headers):
	to_del_param_list = []
        to_del_param_dict = {}
        sys.stdout.write("Failed connections exist\n")
        sys.stdout.write("Retrying for failed connections...\n")
	conn_count = 0
        for i in range(len(param_dict['net_id'])):
            network_id = param_dict['net_id'][i]
            tenant_id = param_dict['tennt_id'][i]
            l2_gateway_id = param_dict['gw_id'][i]
            seg_id = param_dict['seg_id'][i]   
            connectn_id = param_dict['connection_id'][i]  
            for i in range(3):
                sys.stdout.write(("Retry attempt %s...\n") % (i+1))
                if not seg_id :
                    payload = {"l2_gateway_connection": {"network_id": network_id, "l2_gateway_id": l2_gateway_id}}
                    """
                    creating connection
                    """
                    self.log.info("Retrying for connection %s" %(connectn_id))
                    create_conn = requests.post(req_url, data=json.dumps(payload), headers=headers)
                    if create_conn.ok:
                        self.log.info("Connection %s  creation successful" %(connectn_id))
		        break
                else:
                    payload = {"l2_gateway_connection": {"network_id": network_id, "segmentation_id": seg_id ,"l2_gateway_id": l2_gateway_id}}
                    """
                    creating connection
                    """
                    self.log.info("Retrying for connection %s" %(connectn_id))
                    create_conn = requests.post(req_url, data=json.dumps(payload), headers=headers)
                    if create_conn.ok:
                        self.log.info("Connection %s  creation successful" %(connectn_id))
		        break
           
	    if not(create_conn.ok):
                to_del_param_dict = dict()
		to_del_param_dict['network_id'] = network_id
		to_del_param_dict['connectn_id'] = connectn_id
		to_del_param_dict['tenant_id'] = tenant_id
		to_del_param_dict['l2_gateway_id'] = l2_gateway_id
		to_del_param_dict['seg_id'] = seg_id
		to_del_param_list.append(to_del_param_dict)
	    else:
	        conn_count += 1
        if to_del_param_list:	
            self.delete_csv_entries(to_del_param_list)
            sys.stdout.write("Migration NOT Successfull after retry!!!\n")
	else:
	    os.remove(self.DATA_EXC_FILE)
            self.log.info("Connections Created successfully\n")
	    sys.stdout.write("Migration Successfull\n")
        total_conn = len(param_dict['net_id'])
        sys.stdout.write("%s connection created successfully out of %s connections\n"%(str(conn_count),str(total_conn)))
   

    def create_connection(self,param_dict,req_url,headers):
        retry_flag = False
	to_del_param_list = []
        to_del_param_dict = {}
	conn_count = 0
        for i in range(len(param_dict['net_id'])):
            network_id = param_dict['net_id'][i]
            tenant_id = param_dict['tennt_id'][i]
            l2_gateway_id = param_dict['gw_id'][i]
            seg_id = param_dict['seg_id'][i]   
            connectn_id = param_dict['connection_id'][i] 
            if not seg_id :
                payload = {"l2_gateway_connection": {"network_id": network_id, "l2_gateway_id": l2_gateway_id}}
                """
                creating connection
                """
                create_conn = requests.post(req_url, data=json.dumps(payload), headers=headers)
            else:
                payload = {"l2_gateway_connection": {"network_id": network_id, "segmentation_id": seg_id ,"l2_gateway_id": l2_gateway_id}}
                """
                creating connection
                """
                create_conn = requests.post(req_url, data=json.dumps(payload), headers=headers)
            if not(create_conn.ok):
                to_del_param_dict = dict()
                retry_flag = True
		to_del_param_dict['network_id'] = network_id
		to_del_param_dict['connectn_id'] = connectn_id
		to_del_param_dict['tenant_id'] = tenant_id
		to_del_param_dict['l2_gateway_id'] = l2_gateway_id
		to_del_param_dict['seg_id'] = seg_id
		to_del_param_list.append(to_del_param_dict)
                #self.create_failure_file(connectn_id, network_id , tenant_id, seg_id, l2_gateway_id )
            else:
	        conn_count += 1

        if retry_flag == True:
            self.delete_csv_entries(to_del_param_list)
	    param_flddict = self.read_data_file(self.DATA_EXC_FILE)
            self.create_failed_connection(param_flddict,req_url,headers=headers)
	else:
           total_conn = len(param_dict['net_id'])
           sys.stdout.write("%d connection created successfully out of %d connections\n"%(conn_count,total_conn))


    def get_connections_list(self,req_url,headers):
        """
        Fetching connection list available on source
        """
        list_conn = requests.get(req_url, headers=headers)
        connection_list = list_conn.text

        self.log.debug("Fetched connection List: %s" % (connection_list))
        return connection_list

    def get_seg_id(self,l2_gw_id):
        param_dict = self.read_data_file(self.DATA_FILE)
        for i in range(len(param_dict['seg_id'])):
            if param_dict['seg_id'][i]!= '':
                gw_id =  param_dict['gw_id'][i]
		if l2_gw_id ==	gw_id:
                    return param_dict['seg_id'][i] 


    def validate_vlan_bindings(self,req_url,headers):
        gw_list = requests.get(req_url, headers=headers)
        l2_gw_list = gw_list.text
        l2_gw_dict = json.loads(l2_gw_list)
        port_list = []
        mapped_port_list = []
        sw_list = []
        port_dict_bindings,switch_details = self.bind_obj.get_ovsdb_bindings()
        for sw_dict in switch_details:
            switch_port_details = dict()
            switch_port_details['switch_name'] = str(sw_dict['sw_name'].split(':')[1]).replace('\n','')
            switch_port_details['ports'] =  (sw_dict['ports'].split(':')[1]).replace('\n','')
            sw_list.append(switch_port_details)

        for item in   l2_gw_dict['l2_gateways']:
            l2_gw_id = item['id']
            for i in item['devices']:
                switch_name = str(i['device_name'])
                seg_id = i['interfaces'][0]['segmentation_id']
                if not seg_id:
                    seg_id = self.get_seg_id(l2_gw_id)
                port_name = i['interfaces'][0]['name']
                for data in port_dict_bindings:
                    port_id = str(data['port_id'].split(':')[1].replace('\n','')).strip()
		    if port_id not in port_list:
		        port_list.append(port_id)
                    for val in sw_list:
                        if switch_name in val['switch_name'] and port_id in val['ports']:
                            if str(seg_id) in data['bindings'] and port_name in data['name']:
                                mapped_port_list.append(port_id)
        unmapped_port_list = [port for port in port_list if port not in mapped_port_list]
        sw_port_lst = []
	for port in unmapped_port_list:
            for sw in sw_list:
                if port in sw['ports']:
                    sw_port_dct = dict()
                    sw_port_dct['switch_name'] = sw['switch_name']
                    sw_port_dct['ports'] = port
                    sw_port_lst.append(sw_port_dct)
        return sw_port_lst


    def execute_migration(self):
        if not(os.path.isfile(self.DATA_EXC_FILE)): #or os.stat(self.DATA_EXC_FILE).st_size==0:
            """
            Executing L2GW migration steps
            """
            self.log.info("Executing Migration")
            self.log.info("Fetching Connection list")
            count = 0
            try:
                socket.inet_aton(self.host_ip)
                ip_pat = re.findall('\d+\.\d+\.\d+\.\d+$',self.host_ip)
                if not ip_pat:
                    raise migration_exceptions.InvalidIpAddress('IP validation failed')
                req_url = "http://%s:9696/v2.0/l2-gateway-connections.json"  % (self.host_ip)
                headers = self.get_headers()
                
                sys.stdout.write("Step 1. Fetching Connection List\n")
                connection_list = self.get_connections_list(req_url,headers)
                if not connection_list:
                    sys.stdout.write("No connection available on source #### No migration will happen####\n")
                    self.log.info("No Connection available on source #### No migration will happen####")
                    sys.exit()
                else:    
                    self.log.info("Connection list %s" % (connection_list))
                    gw_lst_req_url =  "http://%s:9696/v2.0/l2-gateways.json"  % (self.host_ip)
                    sys.stdout.write("Step 2. Populating data file\n")
                    self.populate_data_file(connection_list)
                    self.log.info("##Datafile populated##")
	                       	    
                    #To autoconfigure neutron db creds: 
                    #self.neutron_obj.fetch_credentials()
                    sys.stdout.write("Step 3. Deleting Entry from MySql\n")
                    db_obj = database_connection.db_connection()
                    self.log.info("##Connected to database##")
                    db_obj.read_connection_uuid()
                    self.log.info("##Deleting connection data from database##")
                    self.log.info("##Creating Connection on destination##")
                    sys.stdout.write("Step 4. Creating Connection\n")
                    param_dict = self.read_data_file(self.DATA_FILE)
                    self.create_connection(param_dict,req_url,headers=headers)
                    if (os.path.isfile(self.DATA_EXC_FILE)): 
                        self.log.info("##Error occurred in migration. Please check failed_switch.csv file for further details##")
                        sys.stdout.write("Migration not completed successfully. Please check logs foe further details\n")
                    else:
                        gw_lst_req_url =  "http://%s:9696/v2.0/l2-gateways.json"  % (self.host_ip)
                        unmapped_ports = self.validate_vlan_bindings(gw_lst_req_url,headers)
		        if unmapped_ports:
		            sys.stdout.write("Migration not Successfull!!!!!! \n")
                            self.log.debug("vlan bindings not created for following switches :%s " %(unmapped_ports))
                            sys.stderr.write("vlan bindings not created for following switches :%s \n" %(unmapped_ports))
                            raise migration_exceptions.NoMappingFound('vlan bindings not created')
		        else:	
                            sys.stdout.write("Migration Successfull!!!!!! \n")
                
                               
            except migration_exceptions.InvalidIpAddress as e:
                self.log.exception("Error in IP address"
                                   "Reason: %s" % (e))
                self.log.debug("Wrong IP address")
                sys.stderr.write(e._error_string+'\n')
                sys.exit()
    
            except socket.error as e:
                sys.stderr.write("IPV4 address validation failed" + '\n')
                self.log.debug("Wrong IPV4 address")
                self.log.exception("Error in IPV4 address"
                                   "Reason: %s" % (e))
                sys.exit()
    
            except (requests.exceptions.HTTPError) as e:
                print "An HTTPError:", e.message
                self.log.debug("HTTP ERROR")
                self.log.exception("An HTTPError:"
                                   "Reason: %s" % (e))
    
            except webob.exc.HTTPError() as e:
                self.log.exception("webob.exc.HTTPError()"
                                   "Reason: %s" % (e))
                self.log.debug("webob.exc.HTTPError")
                raise webob.exc.HTTPError(e)
    
            except migration_exceptions.NoMappingFound as e:
                self.log.debug("Complete Mapping not created")
                self.log.exception("Complete Mapping not created"
                                   "Reason: %s" % (e))
                sys.stderr.write(e._error_string+'\n')
    
            except Exception as e:
                self.log.exception("UnhandeledException :::"
                                   "Reason: %s" % (e))
                raise UnhandeledException(e)
    
            except IOError as e:
                self.log.exception("Invalid config file format"
                                   "Reason: %s" % (e))
                sys.stderr.write("Invalid config file format" + '\n')
                sys.exit()
                
        else:
            param_flddict = self.read_data_file(self.DATA_EXC_FILE)
            req_url = "http://%s:9696/v2.0/l2-gateway-connections.json"  % (self.host_ip)
            headers = self.get_headers()
            self.create_failed_connection(param_flddict,req_url,headers=headers)    
