import socket
import requests
import json
import csv
import os
import sys
#from src.common import migration_exceptions
from src.common import token_generator
from src.common import config
import logging
import webob.exc
from src.common.migration_exceptions import UnhandeledException
import re
from src.common.vtep_add_switch import vtep_command_manager
from src.common.neutron_creds import Neutron_Credentials
import time
from src.db_migration import MigrationScript
from src.common.database_connection import DB_Connection
import MySQLdb


class PerformRestore():

    def __init__(self):
        self.CREDS_FILE = ''.join([''.join([os.getcwd(),'/']), 'creds_file.csv'])
        self.db_user_id = config.CONF.DATABASE_CRED.db_user_id
        self.db_pwd = config.CONF.DATABASE_CRED.db_pwd
        self.db_name = config.CONF.DATABASE_CRED.db_name
        self.db_obj = DB_Connection()
        self.logfile = os.getcwd() + '/log/backup_restore_log.log'
        log_level = logging.INFO
        if config.CONF.default.debug:
            log_level = logging.DEBUG
        self.init_log(self.logfile, log_level, 'backup_restore')
        self.log = logging.getLogger('backup_restore')

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

    
    def unbind_ls(self, switch_name_ovsdb, port_name, ovs_vlan_list,host_ip,user_name,password):
        self.vtep_obj = vtep_command_manager()
        self.client = self.vtep_obj.connect_host(
            str(host_ip),str(user_name),str(password))
        self.log.info("Unbinding VLANS")

        for vlan in ovs_vlan_list:
            exec_unbind_cmd = 'cd /home/ubuntu;./vtep-ctl unbind-ls %s %s %s' % (
                switch_name_ovsdb, port_name, vlan)
            stdin, stdout, stderr = self.client.exec_command(exec_unbind_cmd)
            self.log.info("Unbinded vlan for switch name :%s port_name: %s vlan: %s " % (switch_name_ovsdb, port_name, vlan))

    
    def bind_ls(self, switch_name_ovsdb, port_name, ovs_vlan_list, ls_dict,host_ip,user_name,password):
        self.vtep_obj = vtep_command_manager()
        self.client = self.vtep_obj.connect_host(
            str(host_ip),str(user_name),str(password))
        self.log.info("Binding VLANS")
        for vlan in ovs_vlan_list:
            for key in ls_dict.keys():
                if vlan == key:
                    ls_name = ls_dict[key].replace('\n', '')
                    exec_bind_cmd = 'cd /home/ubuntu;./vtep-ctl bind-ls %s %s %s %s' % (
                        switch_name_ovsdb, port_name.replace('\n', ''), vlan, ls_name)
                    stdin, stdout, stderr = self.client.exec_command(
                        exec_bind_cmd)
                    self.log.info("Unbinded vlan for switch name :%s port_name: %s vlan: %s " % (switch_name_ovsdb, port_name, vlan))

    def get_ls_name(self,ls_id,ls_dict):
        for key in ls_dict.keys():
            if ls_id == key.replace('\n','').strip():
                ls_name = ls_dict[key].replace('\n','')
                return ls_name
        
    
    def compare(self, spv, switch_final):
        self.switch_diff = {}
        self.switch_diff1 = {}
        sw_port = {}
        print "mysql vlan related data...", spv
        print "ovsdb vlan related data...", switch_final
        self.log.info("Comparing the data from MYSQL and OVSDB ")
        for switch in spv:
            if switch_final.has_key(switch):
                self.switch_diff[switch] = {}
                self.switch_diff1[switch] = {}

                for port in spv[switch]:
                    self.switch_diff[switch][port] = list(
                        set(switch_final[switch][port]) - set(spv[switch][port]))

                for port1 in switch_final[switch]:
                    #                import pdb; pdb.set_trace()
                    self.switch_diff1[switch][port1] = list(
                        set(spv[switch][port1]) - set(switch_final[switch][port1]))

                sw_port[switch] = list(
                    set(switch_final[switch]) - set(spv[switch]))

        self.log.info("to be unbinded %s and to be binded %s " % (self.switch_diff,self.switch_diff1))
        return self.switch_diff, self.switch_diff1
    
    
    
    def add_ucast_ovsdb(self,mac,ls_name,ip,host_ip,user_name,password):
        vtep_obj = vtep_command_manager()
        client = vtep_obj.connect_host(str(host_ip),str(user_name),str(password))
        exec_addls_cmd = 'cd /home/ubuntu;./vtep-ctl add-ucast-remote %s %s %s' % (ls_name,mac,ip)
        stdin, stdout, stderr = client.exec_command(exec_addls_cmd)
        
    
    def del_ucast_ovsdb(self,mac,ls_name,host_ip,user_name,password):
        vtep_obj = vtep_command_manager()
        client = vtep_obj.connect_host(str(host_ip),str(user_name),str(password))
        exec_addls_cmd = 'cd /home/ubuntu;./vtep-ctl del-ucast-remote %s %s' % (ls_name,mac)
        stdin, stdout, stderr = client.exec_command(exec_addls_cmd)
    
    
    def get_ls_name_ovsdb(self,ls_id,ls_ovsdb_data):
        for item in ls_ovsdb_data:
            if ls_id in item['uuid']:
                ls_name = item['name'].split(':')[1].replace('\n','').strip()
                return ls_name
    
    
    def compare_ucast_data(self,ucast_mysql_dict,ucast_ovsdb_data,ls_dict,ls_ovsdb_data):
        print "ucast_mysql_dict ....   " , ucast_mysql_dict
        print "ucast_ovsdb_data ....   " , ucast_ovsdb_data
        uuid_to_add = []
        uuid_to_del = []
        #flag = False
        #flag1 = False
        for uuid in ucast_mysql_dict:
            flag = False
            for ovsdb_uuid in ucast_ovsdb_data:
                if str(uuid) in str(ovsdb_uuid['uuid']):
                    flag = True
                    break
    
            if not flag:
                uuid_to_add.append(uuid)
    
        for uuid_dict in ucast_ovsdb_data:
            flag1 = False
            uuid_ovsdb = uuid_dict['uuid'].split(':')[1].replace('\n','').strip()
            for uuid in ucast_mysql_dict:
    
                if str(uuid_ovsdb) in str(uuid):
                    flag1 = True
                    break
            if not flag1:
                uuid_to_del.append(uuid_ovsdb)
        print "uuid to add .....  ",  uuid_to_add
        print "uuid to del .....  ", uuid_to_del
        return uuid_to_add,uuid_to_del,ls_dict,ls_ovsdb_data
    

    def create_bindings(self,bind_vlan_dict,prt_id_name_dict,ls_key_name_dict,host_ip,user_name,password):
        for sw1 in bind_vlan_dict:
                for port in bind_vlan_dict[sw1]:
                    port_name = prt_id_name_dict[port]
     
                    if bind_vlan_dict[sw1][port]:
                        if len(bind_vlan_dict[sw1][port][0]) > 0:
                            vlan_lst = bind_vlan_dict[sw1][port]
                            print "bind data", sw1, port_name, vlan_lst, ls_key_name_dict
                            self.bind_ls(
                                sw1, port_name, vlan_lst, ls_key_name_dict,host_ip,user_name,password)
                            
    def add_ucast_data(self,uuid_to_add,ucast_mysql_dict,ls_dict,host_ip,user_name,password):
        if uuid_to_add:
            for uuid in uuid_to_add:
            #    import pdb;pdb.set_trace()
                for item in ucast_mysql_dict:
                    if uuid in item:
                        mac = ucast_mysql_dict[item][0]
                        ls_id = ucast_mysql_dict[item][1].replace('\n','').strip()
                        ls_name = self.get_ls_name(ls_id,ls_dict)
                        ip = ucast_mysql_dict[item][2].replace('\n','').strip()
                        self.add_ucast_ovsdb(mac,ls_name,ip,host_ip,user_name,password)
                        
    def delete_ucast_data(self,uuid_to_del,ucast_ovsdb_data,ls_ovsdb_data,host_ip,user_name,password):
        if uuid_to_del:
            for uuid in uuid_to_del:
                for item in ucast_ovsdb_data:
                    #import pdb;pdb.set_trace()
                    if uuid in item['uuid']:
                        mac = item['mac'].split(': ')[1].replace('\n','').strip()
                        ls_id = item['logical_switch'].split(':')[1].replace('\n','').strip()
                        ls_name = self.get_ls_name_ovsdb(ls_id,ls_ovsdb_data)
                        self.del_ucast_ovsdb(mac,ls_name,host_ip,user_name,password)
                        
                        
    def unbind_bindings(self,unbind_vlan_dict,port_dict_bindings,ls_key_name_dict,host_ip,user_name,password):
        for sw in unbind_vlan_dict:
            for port in unbind_vlan_dict[sw]:
                for item in port_dict_bindings:
                    if str(item['port_id'].split(':')[1].strip()) == port:
                        port_name = str(item['name'].split(':')[1].strip())
                    if unbind_vlan_dict[sw][port]:
                        if len(unbind_vlan_dict[sw][port][0]) > 0:
                            vlan_lst = unbind_vlan_dict[sw][port]
                            self.unbind_ls(sw,port_name,vlan_lst,host_ip,user_name,password)
    
    
    def execute_restore(self, switch_details, port_vlan, prt_id_name_dict, ls_key_name_dict,port_dict_bindings,uuid_to_add, uuid_to_del,ls_dict,ls_ovsdb_data,ucast_mysql_dict,ucast_ovsdb_data,host_ip,user_name,password):
        self.switch_port_details = dict()
        self.switch_final = {}
        
        for sw_dict in switch_details:
            switch_name = str(sw_dict['sw_name'].split(':')[1]).replace(
                '\n', '').replace('"', '').replace(' ', '')
            port_name = str(sw_dict['ports'].split(':')[1]).replace(
                '\n', '').replace('[', '').replace(']', '').replace(' ', '')
            self.switch_port_details[switch_name] = {}
            self.switch_port_details[switch_name] = port_name.split(',')
            self.switch_final[switch_name] = {}
            if port_name != '':
                for port in self.switch_port_details[switch_name]:
                    self.switch_final[switch_name][port] = []
                    self.switch_final[switch_name][port] = port_vlan[port]
        self.unbind_vlan_dict, self.bind_vlan_dict = self.compare(
            spv, self.switch_final)
       
        self.create_bindings(self.bind_vlan_dict,prt_id_name_dict,ls_key_name_dict,host_ip,user_name,password)
        self.add_ucast_data(uuid_to_add,ucast_mysql_dict,ls_dict,host_ip,user_name,password)
        self.delete_ucast_data(uuid_to_del,ucast_ovsdb_data,ls_ovsdb_data,host_ip,user_name,password)
        self.unbind_bindings(self.unbind_vlan_dict,port_dict_bindings,ls_key_name_dict,host_ip,user_name,password)

    
    def vlan_dict(self, port_dict_bindings, prt_id_name_dict, ls_key_name_dict,uuid_to_add, uuid_to_del,ls_dict,ls_ovsdb_data,ucast_mysql_dict,ucast_ovsdb_data,host_ip,user_name,password):
        port_vlan = {}
        for port_dict in port_dict_bindings:
            port_nm = (port_dict['port_id'].split(':')[1]).replace(
                '\n', '').replace('[', '').replace(']', '').replace(' ', '')
            temp_str = str(port_dict['bindings'].replace(' ', '').replace(
                'vlan_bindings', '').replace('\n', '').replace(':', ''))
            vlist = str(temp_str.split('=')).split(',')
            vlan_list = []
            for ele in vlist:
                if len(ele) < 10:
                    vlan_list.append(ele.replace('{', '').replace('}', '').replace(
                        '\'', '').replace('\"', '').replace('[', '').replace(']', ''))
            port_vlan[port_nm] = vlan_list
        self.execute_restore(
            switch_details, port_vlan, prt_id_name_dict, ls_key_name_dict,port_dict_bindings,uuid_to_add, uuid_to_del,ls_dict,ls_ovsdb_data,ucast_mysql_dict,ucast_ovsdb_data,host_ip,user_name,password)

    
    def fetch_t1_timestamp_data(self):

        client = self.db_obj.connect_host()

        switch_query = 'sudo mysql -e "select physical_switches.uuid , physical_switches.name from physical_switches;" -u %s -p%s %s' % (
            self.db_user_id, self.db_pwd, self.db_name)
        sw_port_query = 'sudo mysql -e "select physical_switches.uuid , physical_switches.name , physical_ports.uuid, physical_ports.name from physical_switches join physical_ports ON physical_switches.uuid = physical_ports.physical_switch_id;"  -u %s -p%s %s' % (
            self.db_user_id, self.db_pwd, self.db_name)

        sw_port_vlan_query = 'sudo mysql -e "select physical_switches.uuid , physical_switches.name , physical_ports.uuid, physical_ports.name, vlan_bindings.vlan from physical_switches join physical_ports ON physical_switches.uuid = physical_ports.physical_switch_id JOIN vlan_bindings ON physical_ports.uuid = vlan_bindings.port_uuid;" -u %s -p%s %s' % (
            self.db_user_id, self.db_pwd, self.db_name)
        
        ucast_query = 'sudo mysql -e "select ucast_macs_remotes.uuid,ucast_macs_remotes.mac,ucast_macs_remotes.logical_switch_id, ucast_macs_remotes.ip_address from ucast_macs_remotes;" -u %s -p%s %s' % (self.db_user_id,self.db_pwd,self.db_name)

        ls_id_dict = {}
        ls_key_name_dict = {}
        
        ls_data_query = 'sudo mysql -e "select logical_switches.key ,logical_switches.name,logical_switches.uuid from logical_switches;"  -u %s -p%s %s' % (
            self.db_user_id, self.db_pwd, self.db_name)

        try:
            stdin, stdout, stderr = client.exec_command(ls_data_query)
            for line in stdout:
                if 'key' in line:
                    continue
                key = str(line.replace('\n','').split('\t')[0])
                ls_key_name = str(line.split('\t')[1])
                ls_key_uuid = str(line.split('\t')[2])
                ls_key_name_dict[key] = ls_key_name
                ls_id_dict[ls_key_uuid] = ls_key_name
        except MySQLdb.Error as ex:
            print ex

        ucast_data_dict = {}
        
	try:
            stdin, stdout, stderr = client.exec_command(ucast_query)
            for line in stdout:
                if 'uuid' in line:
                    continue
                ucast_detail_list=[]
                ucast_uuid = str(line.replace('\n','').split('\t')[0])
                mac = str(line.split('\t')[1])
                logical_switch_id = str(line.split('\t')[2])
                ip_address = str(line.split('\t')[3])
                ucast_detail_list.append(mac)
                ucast_detail_list.append(logical_switch_id)
                ucast_detail_list.append(ip_address)
                ucast_data_dict[ucast_uuid] = ucast_detail_list
            #print "ucast.....",ucast_data_dict
        except MySQLdb.Error as ex:
            print ex


        spv = {}
        prt_id_name_dict = {}
        
        #spv_vlan_list = []
        try:
            stdin, stdout, stderr = client.exec_command(sw_port_vlan_query)
            for line in stdout:
                if 'uuid' in line:
                    continue
                vlan_id = str(line.replace('\n','').split('\t')[4])
                sw_id = str(line.split('\t')[1])
                port_id = str(line.split('\t')[2])
                port_name = str(line.split('\t')[3])
                prt_id_name_dict[port_id] = port_name
                if  spv.setdefault(sw_id,{}).has_key(port_id):
                    spv.setdefault(sw_id,{})[port_id].append(vlan_id)
                else:
                    spv.setdefault(sw_id,{})[port_id] = [vlan_id]
        except MySQLdb.Error as ex:
            print ex


        port_list = []
        sw_port_dict = {}

        try:
            stdin, stdout, stderr = client.exec_command(sw_port_query)
            for line in stdout:
                if 'uuid' in line:
                    continue
                sw_id = str(line.split('\t')[1])
                port_id = str(line.split('\t')[2])
                port_name = str(line.split('\t')[3])
                prt_id_name_dict[port_id] = port_name
                sw_port_dict.setdefault(sw_id, []).append(port_id)
#               print sw_port_dict

        except MySQLdb.Error as ex:
            print ex

        sw_list = []
        try:
            stdin, stdout, stderr = client.exec_command(switch_query)
            for line in stdout:
                uuid = str(line.split()[1])
                sw_list.append(uuid)
            sw_list.pop(0)
#       print sw_list
        except MySQLdb.Error as ex:
            print ex

        for sw in sw_list:
            if sw not in sw_port_dict.keys():
                sw_port_dict.setdefault(sw,[])
#    print sw_port_dict

        for sw in sw_port_dict.keys():
            if sw not in spv.keys():
                temp = {}
                for value in sw_port_dict[sw]:
                    temp[value]=[]
                spv[sw]=temp
            else:
                for value in sw_port_dict[sw]:
                    port = spv[sw]
                    if value not in port.keys():
                        port[value]=[]

        return spv,prt_id_name_dict,ls_key_name_dict,ucast_data_dict,ls_id_dict


    
    def get_ovsdb_data(self,host_ip,user_name,password):
        #mig_obj = MigrationScript()
        #host_ip = '10.8.20.51'
        #req_url = "http://%s:9696/v2.0/l2-gateways.json" % (host_ip)
        #headers = mig_obj.get_headers()
        #gw_list = requests.get(req_url, headers=headers)
        #l2_gw_list = gw_list.text
        #l2_gw_dict = json.loads(l2_gw_list)
        #port_list = []
        #mapped_port_list = []
        #sw_list = []
        #spv = {}
        vtep_obj = vtep_command_manager()
        port_dict_bindings, switch_details = vtep_obj.get_ovsdb_bindings(host_ip,user_name,password)
        return port_dict_bindings, switch_details

    
    def get_ovsdb_creds(self):
        """
        Populating csv data file
        """
        '''
        try:
            with open(self.CREDS_FILE, 'wb') as fp:
                writer = csv.writer(fp, delimiter=',')
                dict1 = {'host1':['10.8.20.112','root','ubuntu'],'host2':['10.8.20.113','root','ubuntu']}
                writer.writerow(["switch_ip", "user_name", "password"])
                for item in dict1:
                    data = dict1[item]
                    print data
                    writer.writerow([data[0],data[1],data[2]])
        except IOError as ex:
            sys.stdout.write("Error in writing csv file:", self.CREDS_FILE)
        '''     
        """
        Reading csv data file
        """
        creds_list = []
        with open(self.CREDS_FILE, 'rb') as fp:
            reader = csv.reader(fp, delimiter=',')
            for row in reader:
                if 'switch_ip' in row:
                    continue
                else:
                    creds_list.append(row)
            return creds_list


if __name__ == '__main__':
    perfrest = PerformRestore()
    spv, prt_id_name_dict, ls_key_name_dict,ucast_mysql_dict,ls_id_dict = perfrest.fetch_t1_timestamp_data()
    vtep_obj = vtep_command_manager()
    creds_list = perfrest.get_ovsdb_creds()
    for cred_list in creds_list:
        
        port_dict_bindings = []
        switch_details = []
        ucast_ovsdb_data = []
        ls_ovsdb_data = []
        
        host_ip =  cred_list[0]
        user_name = cred_list[1]
        password = cred_list[2]
    
        #import pdb;pdb.set_trace()
        port_dict_bindings, switch_details = perfrest.get_ovsdb_data(host_ip,user_name,password)
    
        ucast_ovsdb_data = vtep_obj.get_ucast_data(host_ip,user_name,password)
        ls_ovsdb_data = vtep_obj.get_ls_data(host_ip,user_name,password)
        
        uuid_to_add, uuid_to_del,ls_dict,ls_ovsdb_data = perfrest.compare_ucast_data(ucast_mysql_dict,ucast_ovsdb_data,ls_id_dict,ls_ovsdb_data)
        
        perfrest.vlan_dict(port_dict_bindings, prt_id_name_dict, ls_key_name_dict,uuid_to_add, uuid_to_del,ls_dict,ls_ovsdb_data,ucast_mysql_dict,ucast_ovsdb_data,host_ip,user_name,password)

    










