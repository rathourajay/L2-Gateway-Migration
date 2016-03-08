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

class MigrationScript(object):

    def __init__(self):
        
        self.DATA_FILE = ''.join([''.join([os.getcwd(),'/data/']), 'data_file.csv'])
        self.DATA_EXC_FILE = ''.join([''.join([os.getcwd(),'/data/']), 'data_exc_file.csv'])
        self.controller_ip = config.CONF.default.controller_ip
        self.username = config.CONF.OPENSTACK_CREDS.username
        self.password =  config.CONF.OPENSTACK_CREDS.password
        self.tenant_name =  config.CONF.OPENSTACK_CREDS.tenant_name
        log_level = logging.INFO
        if config.CONF.default.debug:
            log_level = logging.DEBUG
        self.init_log(config.CONF.OPENSTACK_CREDS.log_file, log_level, 'l2_gateway')
        self.log = logging.getLogger('l2_gateway')
        self.bind_obj = vtep_command_manager()

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
        auth_token = token_generator.get_user_token(self.username,self.password,self.tenant_name,self.controller_ip)

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
                import pdb;pdb.set_trace()
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
            print "Error in writing csv file:", data_file
            self.log.exception("Error in writing csv file: %s. "
                               "Reason: %s" % (data_file, ex))
            sys.stdout.write(_("Error in writing csv file: %s. "
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
            print "Error in reading csv file:", conn_file
            self.log.exception("Error in reading csv file: %s. "
                               "Reason: %s" % (conn_file, ex))
            sys.stdout.write(_("Error in reading csv file: %s. "
                               "Reason: %s\n") % (conn_file, ex))
 
        self.log.info("Content extracted from data file %s" % (param_dict))
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

    def create_failure_file(self,connectn_id, network_id , tenant_id, seg_id, l2_gateway_id):
        failure_file = self.DATA_EXC_FILE
        try: 
            with open(failure_file, 'a') as fep:
                writer1 = csv.writer(fep, delimiter='\t')
                writer1.writerow(["connection_id", "network_id", "tenant_id", "l2_gateway_id", "segmentation_id"])
                writer1.writerow([connectn_id, network_id, tenant_id, l2_gateway_id, seg_id])
        except IOError as ex:
            print "Error in writing failure file:", data_file
            self.log.exception("Error in writing csv file: %s. "
                               "Reason: %s" % (data_file, ex))
            sys.stdout.write(_("Error in writing csv file: %s. "
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
            self.log.exception("Error in writing csv file: %s. "
                               "Reason: %s" % (data_file, ex))
            sys.stdout.write(_("Error in writing csv file: %s. "
                               "Reason: %s\n") % (data_file, ex))



    def create_failed_connection(self,param_dict,req_url,headers):
	to_del_param_list = []
        to_del_param_dict = {}
        for i in range(len(param_dict['net_id'])):
            network_id = param_dict['net_id'][i]
            tenant_id = param_dict['tennt_id'][i]
            l2_gateway_id = param_dict['gw_id'][i]
            seg_id = param_dict['seg_id'][i]   
            connectn_id = param_dict['connection_id'][i]  
            for i in range(3):
                if not seg_id :
                    payload = {"l2_gateway_connection": {"network_id": network_id, "l2_gateway_id": l2_gateway_id}}
                    """
                    creating connection
                    """
                    create_conn = requests.post(req_url, data=json.dumps(payload), headers=headers)
                    if create_conn.ok:
		        break
                else:
                    payload = {"l2_gateway_connection": {"network_id": network_id, "segmentation_id": seg_id ,"l2_gateway_id": l2_gateway_id}}
                    """
                    creating connection
                    """
                    create_conn = requests.post(req_url, data=json.dumps(payload), headers=headers)
                    if create_conn.ok:
		        break
	    if not(create_conn.ok):
		to_del_param_dict['network_id'] = network_id
		to_del_param_dict['connectn_id'] = connectn_id
		to_del_param_dict['tenant_id'] = tenant_id
		to_del_param_dict['l2_gateway_id'] = l2_gateway_id
		to_del_param_dict['seg_id'] = seg_id
		to_del_param_list.append(to_del_param_dict)
        if to_del_param_list:	
            self.delete_csv_entries(to_del_param_list)
	else:
	    os.remove(self.DATA_EXC_FILE)
	    print "file deleted"



    def create_connection(self,param_dict,req_url,headers):
        retry_flag = False
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
                retry_flag = True
                self.create_failure_file(connectn_id, network_id , tenant_id, seg_id, l2_gateway_id )
        
        if retry_flag == True:
	    param_flddict = self.read_data_file(self.DATA_EXC_FILE)
            self.create_failed_connection(param_flddict,req_url,headers=headers)

            
        self.log.info("Creating connection with command %s" %(create_conn.text))
        self.log.info("connection created")
        
            

    def retry_create_connection(self,param_dict,req_url,headers,create_conn):
        flag = True
        for i in range(3):
            create_conn = self.create_connection(param_dict,req_url,headers)
            if not create_conn.ok:
                flag = False
                continue
            else:
	        break
        if not flag:
            self.create_failure_file(connectn_id, network_id , tenant_id, seg_id, l2_gateway_id )


    def get_connections_list(self,req_url,headers):
        """
        Fetching connection list available on source
        """
        list_conn = requests.get(req_url, headers=headers)
        connection_list = list_conn.text

        self.log.debug("Fetched connection List: %s" % (connection_list))
        return connection_list


    def validate_vlan_bindings(self,req_url,headers):
        """
        TO DO: raise user define exception in place of else.
        """
        gw_list = requests.get(req_url, headers=headers)
        l2_gw_list = gw_list.text
        l2_gw_dict = json.loads(l2_gw_list)
        port_list = []
        mapped_port_list = []

        port_dict_bindings = self.bind_obj.get_ovsdb_bindings()
        for item in   l2_gw_dict['l2_gateways']:
            for i in item['devices']:
                seg_id = i['interfaces'][0]['segmentation_id']
                port_name = i['interfaces'][0]['name']
                if port_name not in port_list:
                    port_list.append(port_name)
                for data in port_dict_bindings:
                    if str(seg_id) in data['bindings'] and port_name in data['name']:
                        print port_name, str(seg_id),"mapped with vlan"
                        mapped_port_list.append(port_name)
        unmapped_port_list = [port for port in port_list if port not in mapped_port_list]
        print unmapped_port_list 
        if  unmapped_port_list:
            raise migration_exceptions.NoMappingFound('vlan bindings not created')
    '''
    def execute_migration(self):
	"""
        Executing L2GW migration steps
        """
        self.log.info("Executing Migration")
        self.log.info("Fetching Connection list")
        count = 0 
        try:
            socket.inet_aton(self.controller_ip)
            ip_pat = re.findall('\d+\.\d+\.\d+\.\d+$',self.controller_ip)
            if not ip_pat:
                raise migration_exceptions.InvalidIpAddress('IP validation failed')
            req_url = "http://%s:9696/v2.0/l2-gateway-connections.json"  % (self.controller_ip)
            headers = self.get_headers()
            
            sys.stdout.write("1. Fetching Connection List\n")
            connection_list = self.get_connections_list(req_url,headers)
            self.log.info("Connection list %s" % (connection_list))
            gw_lst_req_url =  "http://%s:9696/v2.0/l2-gateways.json"  % (self.controller_ip) 
            #self.validate_vlan_bindings(gw_lst_req_url,headers)       
            
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
            param_dict = self.read_data_file(self.DATA_FILE)
            self.create_connection(param_dict,req_url,headers=headers)        
            
            self.log.info("##Connection created on destination##")
            sys.stdout.write("5. Connection created successfully\n")
            #self.update_l2gwagent_ini()
            """
            gw_lst_req_url =  "http://%s:9696/v2.0/l2-gateways.json"  % (self.controller_ip) 
            self.validate_vlan_bindings(gw_lst_req_url,headers)       
            """        
        except migration_exceptions.InvalidIpAddress as e:
            self.log.exception("Error in IP address"
                               "Reason: %s" % (e))
            sys.stderr.write(e._error_string+'\n')
            sys.exit()

        except socket.error as e:
            sys.stderr.write("IPV4 address validation failed" + '\n')
            self.log.exception("Error in IPV4 address"
                               "Reason: %s" % (e))
            sys.exit()

        except (requests.exceptions.HTTPError) as e:
            print "An HTTPError:", e.message
            self.log.exception("An HTTPError:"
                               "Reason: %s" % (e))

        except webob.exc.HTTPError() as e:
            self.log.exception("webob.exc.HTTPError()"
                               "Reason: %s" % (e))
            raise webob.exc.HTTPError(e)
        
        except migration_exceptions.NoMappingFound as e:
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
    '''

    def execute_migration(self):
        import pdb;pdb.set_trace()
        if not(os.path.isfile(self.DATA_EXC_FILE)): #or os.stat(self.DATA_EXC_FILE).st_size==0:
            """
            Executing L2GW migration steps
            """
            self.log.info("Executing Migration")
            self.log.info("Fetching Connection list")
            count = 0
            try:
                socket.inet_aton(self.controller_ip)
                ip_pat = re.findall('\d+\.\d+\.\d+\.\d+$',self.controller_ip)
                if not ip_pat:
                    raise migration_exceptions.InvalidIpAddress('IP validation failed')
                req_url = "http://%s:9696/v2.0/l2-gateway-connections.json"  % (self.controller_ip)
                headers = self.get_headers()
    
                sys.stdout.write("1. Fetching Connection List\n")
                connection_list = self.get_connections_list(req_url,headers)
                self.log.info("Connection list %s" % (connection_list))
                gw_lst_req_url =  "http://%s:9696/v2.0/l2-gateways.json"  % (self.controller_ip)
                #self.validate_vlan_bindings(gw_lst_req_url,headers)
    
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
                param_dict = self.read_data_file(self.DATA_FILE)
                import pdb;pdb.set_trace()
                self.create_connection(param_dict,req_url,headers=headers)
    
                self.log.info("##Connection created on destination##")
                sys.stdout.write("5. Connection created successfully\n")
                #self.update_l2gwagent_ini()
                """
                gw_lst_req_url =  "http://%s:9696/v2.0/l2-gateways.json"  % (self.controller_ip)
                self.validate_vlan_bindings(gw_lst_req_url,headers)
                
                """
                
            except migration_exceptions.InvalidIpAddress as e:
                self.log.exception("Error in IP address"
                                   "Reason: %s" % (e))
                sys.stderr.write(e._error_string+'\n')
                sys.exit()
    
            except socket.error as e:
                sys.stderr.write("IPV4 address validation failed" + '\n')
                self.log.exception("Error in IPV4 address"
                                   "Reason: %s" % (e))
                sys.exit()
    
            except (requests.exceptions.HTTPError) as e:
                print "An HTTPError:", e.message
                self.log.exception("An HTTPError:"
                                   "Reason: %s" % (e))
    
            except webob.exc.HTTPError() as e:
                self.log.exception("webob.exc.HTTPError()"
                                   "Reason: %s" % (e))
                raise webob.exc.HTTPError(e)
    
            except migration_exceptions.NoMappingFound as e:
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
            self.create_connection(param_flddict,req_url,headers=headers)    
            

                                                                
