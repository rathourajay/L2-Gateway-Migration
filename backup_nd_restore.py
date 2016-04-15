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
from src.common.vtep_add_switch import vtep_command_manager


class PerformRestore():

    def __init__(self):
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



    
    def unbind_ls(self, switch_name_ovsdb, port_name, ovs_vlan_list):
        self.vtep_obj = vtep_command_manager()
        self.client = self.vtep_obj.connect_host(
            '10.8.20.112', 'root', 'ubuntu')
        self.log.info("Unbinding VLANS")

        for vlan in ovs_vlan_list:
#	    import pdb;pdb.set_trace()
            exec_unbind_cmd = 'cd /home/ubuntu;./vtep-ctl unbind-ls %s %s %s' % (
                switch_name_ovsdb, port_name, vlan)
            stdin, stdout, stderr = self.client.exec_command(exec_unbind_cmd)
            self.log.info("Unbinded vlan for switch name :%s port_name: %s vlan: %s " % (switch_name_ovsdb, port_name, vlan))

    
    def bind_ls(self, switch_name_ovsdb, port_name, ovs_vlan_list, ls_dict):
        self.vtep_obj = vtep_command_manager()
        self.client = self.vtep_obj.connect_host(
            '10.8.20.112', 'root', 'ubuntu')
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

    #    print "Unbinding vlan binding"

    
    def del_port(self, switch_name_ovsdb, port_name):
        self.vtep_obj = vtep_command_manager()
        self.client = self.vtep_obj.connect_host(
            '10.8.20.112', 'root', 'ubuntu')
        self.log.info("Deleting PORTS")
        exec_unbind_cmd = 'cd /home/ubuntu;./vtep-ctl del-port %s %s' % (
            switch_name_ovsdb, port_name)
        stdin, stdout, stderr = self.client.exec_command(exec_unbind_cmd)
        self.log.info("Deleted port for switch name :%s port_name: %s " % (switch_name_ovsdb, port_name))
    #    print "Deleting ports"

    
    def compare(self, spv, switch_final):
        self.switch_diff = {}
        self.switch_diff1 = {}
        sw_port = {}
        print "spv", spv
        print "ovsdb data", switch_final
        self.log.info("Comparing the data from MYSQL and OVSDB ")
        for switch in spv:
            if switch_final.has_key(switch):
                self.switch_diff[switch] = {}
                self.switch_diff1[switch] = {}
 #               if not spv[switch]:
 #                   sw_port[switch] = switch_final[switch]

                for port in spv[switch]:
                    self.switch_diff[switch][port] = list(
                        set(switch_final[switch][port]) - set(spv[switch][port]))

                for port1 in switch_final[switch]:
                    #                import pdb; pdb.set_trace()
                    self.switch_diff1[switch][port1] = list(
                        set(spv[switch][port1]) - set(switch_final[switch][port1]))

                sw_port[switch] = list(
                    set(switch_final[switch]) - set(spv[switch]))
  #      print self.switch_diff1


        self.log.info("to be unbinded %s and to be binded %s " % (self.switch_diff,self.switch_diff1))
        return self.switch_diff, self.switch_diff1

    
    def switch_dict(self, switch_details, port_vlan, prt_id_name_dict, ls_key_name_dict,port_dict_bindings):
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
        
        for sw in self.unbind_vlan_dict:
            for port in self.unbind_vlan_dict[sw]:
                for item in port_dict_bindings:
                    if str(item['port_id'].split(':')[1].strip()) == port:
                        port_name = str(item['name'].split(':')[1].strip())
                    if self.unbind_vlan_dict[sw][port]:
                        if len(self.unbind_vlan_dict[sw][port][0]) > 0:
                            vlan_lst = self.unbind_vlan_dict[sw][port]
                            # print "unbind data" , sw,port,vlan_lst
                            self.unbind_ls(sw, port_name, vlan_lst)
    #    for sw_data in del_port_dict:
    #        if del_port_dict[sw_data]:
    #            for port_id in del_port_dict[sw_data]:
                 #   for item in port_dict_bindings:
                  #      if str(item['port_id'].split(':')[1].strip()) == port_id:
                  #          port_name =  str(item['name'].split(':')[1].strip())
                   #         del_port(sw_data, port_name)

        for sw1 in self.bind_vlan_dict:
            for port in self.bind_vlan_dict[sw1]:
                port_name = prt_id_name_dict[port]

                if self.bind_vlan_dict[sw1][port]:
                    if len(self.bind_vlan_dict[sw1][port][0]) > 0:
                        vlan_lst = self.bind_vlan_dict[sw1][port]
                        print "bind data", sw1, port_name, vlan_lst, ls_key_name_dict
                        self.bind_ls(
                            sw1, port_name, vlan_lst, ls_key_name_dict)

    
    def vlan_dict(self, port_dict_bindings, prt_id_name_dict, ls_key_name_dict):
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
        self.switch_dict(
            switch_details, port_vlan, prt_id_name_dict, ls_key_name_dict,port_dict_bindings)

    
    def fetch_t1_timestamp_data(self):

        client = self.db_obj.connect_host()

        switch_query = 'sudo mysql -e "select physical_switches.uuid , physical_switches.name from physical_switches;" -u %s -p%s %s' % (
            self.db_user_id, self.db_pwd, self.db_name)
        sw_port_query = 'sudo mysql -e "select physical_switches.uuid , physical_switches.name , physical_ports.uuid, physical_ports.name from physical_switches join physical_ports ON physical_switches.uuid = physical_ports.physical_switch_id;"  -u %s -p%s %s' % (
            self.db_user_id, self.db_pwd, self.db_name)

        sw_port_vlan_query = 'sudo mysql -e "select physical_switches.uuid , physical_switches.name , physical_ports.uuid, physical_ports.name, vlan_bindings.vlan from physical_switches join physical_ports ON physical_switches.uuid = physical_ports.physical_switch_id JOIN vlan_bindings ON physical_ports.uuid = vlan_bindings.port_uuid;" -u %s -p%s %s' % (
            self.db_user_id, self.db_pwd, self.db_name)

        ls_key_name_dict = {}
        ls_data_query = 'sudo mysql -e "select logical_switches.key ,logical_switches.name from logical_switches;"  -u %s -p%s %s' % (
            self.db_user_id, self.db_pwd, self.db_name)
        try:
            stdin, stdout, stderr = client.exec_command(ls_data_query)
            for line in stdout:
                if 'key' in line:
                    continue
                key = str(line.replace('\n', '').split('\t')[0])
                ls_key_name = str(line.split('\t')[1])
                ls_key_name_dict[key] = ls_key_name
        except MySQLdb.Error as ex:
            print ex

        spv = {}
        prt_id_name_dict = {}
        try:
            stdin, stdout, stderr = client.exec_command(sw_port_vlan_query)
            for line in stdout:
                if 'uuid' in line:
                    continue
                vlan_id = str(line.replace('\n', '').split('\t')[4])
                sw_id = str(line.split('\t')[1])
                port_id = str(line.split('\t')[2])
                port_name = str(line.split('\t')[3])
                prt_id_name_dict[port_id] = port_name
                print port_name
                if spv.setdefault(sw_id, {}).has_key(port_id):
                    spv.setdefault(sw_id, {})[port_id].append(vlan_id)
                else:
                    spv.setdefault(sw_id, {})[port_id] = [vlan_id]
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
                sw_port_dict.setdefault(sw, [])

        for sw in sw_port_dict.keys():
            if sw not in spv.keys():
                temp = {}
                for value in sw_port_dict[sw]:
                    temp[value] = []
                spv[sw] = temp
            else:
                for value in sw_port_dict[sw]:
                    port = spv[sw]
                    if value not in port.keys():
                        port[value] = []

        return spv, prt_id_name_dict, ls_key_name_dict

    
    def get_ovsdb_data(self):
        mig_obj = MigrationScript()
        host_ip = '10.8.20.51'
        req_url = "http://%s:9696/v2.0/l2-gateways.json" % (host_ip)
        headers = mig_obj.get_headers()
        gw_list = requests.get(req_url, headers=headers)
        l2_gw_list = gw_list.text
        l2_gw_dict = json.loads(l2_gw_list)
        port_list = []
        mapped_port_list = []
        sw_list = []
        spv = {}
        vtep_obj = vtep_command_manager()
        port_dict_bindings, switch_details = vtep_obj.get_ovsdb_bindings()
        return port_dict_bindings, switch_details


if __name__ == '__main__':
    perfrest = PerformRestore()
    spv, prt_id_name_dict, ls_key_name_dict = perfrest.fetch_t1_timestamp_data()
#    print "mysql data", spv
    port_dict_bindings, switch_details = perfrest.get_ovsdb_data()
#    print "port_dict_bindings" , port_dict_bindings
#    print "switch_details" , switch_details
    perfrest.vlan_dict(port_dict_bindings, prt_id_name_dict, ls_key_name_dict)

