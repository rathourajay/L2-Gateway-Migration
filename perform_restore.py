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

def unbind_ls(switch_name_ovsdb,port_name,ovs_vlan_list):
    vtep_obj = vtep_command_manager()
    client = vtep_obj.connect_host('10.8.20.112','root','ubuntu')
#    switch_name_ovsdb = "test_switch1"
#    port_id = "test_port1"
#    vlan = 1104
    for vlan in ovs_vlan_list:
        exec_unbind_cmd = 'cd /home/ubuntu;./vtep-ctl unbind-ls %s %s %s' % (switch_name_ovsdb,port_name,vlan)
        stdin, stdout, stderr = client.exec_command(exec_unbind_cmd)
#    print "Unbinding vlan binding"

def del_port(switch_name_ovsdb,port_name):
    vtep_obj = vtep_command_manager()
    client = vtep_obj.connect_host('10.8.20.112','root','ubuntu')
    exec_unbind_cmd = 'cd /home/ubuntu;./vtep-ctl del-port %s %s' % (switch_name_ovsdb,port_name)
    stdin, stdout, stderr = client.exec_command(exec_unbind_cmd)
#    print "Deleting ports"

def compare(spv,switch_final):
    switch_diff={}
    switch_diff1={}
    sw_port  ={}
    print "spv",spv
    print "ovsdb data",switch_final
    for switch in spv:
        if switch_final.has_key(switch):
            switch_diff[switch]={}
            switch_diff1[switch]={}
            if not spv[switch]:
                sw_port[switch]=switch_final[switch]
               
            for port in spv[switch]:
                switch_diff[switch][port]=list(set(switch_final[switch][port]) - set(spv[switch][port]))

            for port1 in switch_final[switch]:
#                import pdb; pdb.set_trace()
                switch_diff1[switch][port1]=list(set(spv[switch][port1]) - set(switch_final[switch][port1]))
		
	    sw_port[switch]=list(set(switch_final[switch]) - set(spv[switch]))
    print switch_diff1
    return switch_diff,sw_port,switch_diff1
            

def switch_dict(switch_details,port_vlan):
    switch_port_details = dict()
    switch_final = {}
    for sw_dict in switch_details:
        switch_name = str(sw_dict['sw_name'].split(':')[1]).replace('\n','').replace('"','').replace(' ','')
        port_name= str(sw_dict['ports'].split(':')[1]).replace('\n','').replace('[','').replace(']','').replace(' ','')
        switch_port_details[switch_name] = {}
        switch_port_details[switch_name]= port_name.split(',')
        switch_final[switch_name] = {}
        if port_name !='':
            for port in switch_port_details[switch_name]:
                switch_final[switch_name][port]=[]
                switch_final[switch_name][port]=port_vlan[port]
    unbind_vlan_dict,del_port_dict,bind_vlan_dict = compare(spv,switch_final)

   # print "vlan to unbind",unbind_vlan_dict
#    print "port to delete",del_port_dict
    
    for sw in unbind_vlan_dict:
        for port in unbind_vlan_dict[sw]:
            for item in port_dict_bindings:
                if str(item['port_id'].split(':')[1].strip()) == port:
                    port_name =  str(item['name'].split(':')[1].strip())
                if unbind_vlan_dict[sw][port]:
                    if len(unbind_vlan_dict[sw][port][0])>0:
                        vlan_lst =  unbind_vlan_dict[sw][port]
                        #print "unbind data" , sw,port,vlan_lst
                        unbind_ls(sw,port_name,vlan_lst)
#    for sw_data in del_port_dict:
#        if del_port_dict[sw_data]:
#            for port_id in del_port_dict[sw_data]:
             #   for item in port_dict_bindings:
              #      if str(item['port_id'].split(':')[1].strip()) == port_id:
              #          port_name =  str(item['name'].split(':')[1].strip())
               #         del_port(sw_data, port_name)
       


    for sw1 in bind_vlan_dict:
        for port in bind_vlan_dict[sw1]:
            for item in port_dict_bindings:
                if str(item['port_id'].split(':')[1].strip()) == port:
                    port_name =  str(item['name'].split(':')[1].strip())
                if unbind_vlan_dict[sw][port]:
                    if len(unbind_vlan_dict[sw][port][0])>0:
                        vlan_lst =  unbind_vlan_dict[sw][port]
                        #print "unbind data" , sw,port,vlan_lst
                        unbind_ls(sw,port_name,vlan_lst)
    



def vlan_dict(port_dict_bindings):
    port_vlan = {}
    for port_dict in port_dict_bindings:
        port_nm = (port_dict['port_id'].split(':')[1]).replace('\n','').replace('[','').replace(']','').replace(' ','')
        temp_str = str(port_dict['bindings'].replace(' ','').replace('vlan_bindings','').replace('\n','').replace(':',''))
        vlist = str(temp_str.split('=')).split(',')
        vlan_list=[]
        for ele in vlist:
            if len(ele) <10:
                vlan_list.append(ele.replace('{','').replace('}','').replace('\'','').replace('\"','').replace('[','').replace(']',''))
        port_vlan[port_nm]=vlan_list
    switch_dict(switch_details,port_vlan)


def fetch_t1_timestamp_data():
    db_user_id = config.CONF.DATABASE_CRED.db_user_id
    db_pwd = config.CONF.DATABASE_CRED.db_pwd
    db_name = config.CONF.DATABASE_CRED.db_name
    db_obj = DB_Connection()
    client = db_obj.connect_host()

    switch_query =  'sudo mysql -e "select physical_switches.uuid , physical_switches.name from physical_switches;" -u %s -p%s %s' % (db_user_id,db_pwd,db_name)
    sw_port_query =  'sudo mysql -e "select physical_switches.uuid , physical_switches.name , physical_ports.uuid, physical_ports.name from physical_switches join physical_ports ON physical_switches.uuid = physical_ports.physical_switch_id;"  -u %s -p%s %s' % (db_user_id,db_pwd,db_name)
    
    sw_port_vlan_query = 'sudo mysql -e "select physical_switches.uuid , physical_switches.name , physical_ports.uuid, physical_ports.name, vlan_bindings.vlan from physical_switches join physical_ports ON physical_switches.uuid = physical_ports.physical_switch_id JOIN vlan_bindings ON physical_ports.uuid = vlan_bindings.port_uuid;" -u %s -p%s %s' % (db_user_id,db_pwd,db_name)
    
    spv = {}
    #spv_vlan_list = []
    try:
        stdin, stdout, stderr = client.exec_command(sw_port_vlan_query)
        for line in stdout:
            if 'uuid' in line:
                continue
	    vlan_id = str(line.replace('\n','').split('\t')[4])
            sw_id = str(line.split('\t')[1])
            port_id = str(line.split('\t')[2])
           # import pdb; pdb.set_trace()
            if  spv.setdefault(sw_id,{}).has_key(port_id):
                spv.setdefault(sw_id,{})[port_id].append(vlan_id)
            else:
                spv.setdefault(sw_id,{})[port_id] = [vlan_id]
       # print spv
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
            sw_port_dict.setdefault(sw_id, []).append(port_id)
#        print sw_port_dict
        
    except MySQLdb.Error as ex:
        print ex
    
    sw_list = []
    try:
        stdin, stdout, stderr = client.exec_command(switch_query)
        for line in stdout:
	    uuid = str(line.split()[1])
	    sw_list.append(uuid)
        sw_list.pop(0)
#	print sw_list
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

    return spv

def get_ovsdb_data():
    mig_obj = MigrationScript()
    host_ip = '10.8.20.51'
    req_url =  "http://%s:9696/v2.0/l2-gateways.json"  % (host_ip)
    headers = mig_obj.get_headers()
    gw_list = requests.get(req_url, headers=headers)
    l2_gw_list = gw_list.text
    l2_gw_dict = json.loads(l2_gw_list)
    port_list = []
    mapped_port_list = []
    sw_list = []
    spv = {}
    vtep_obj = vtep_command_manager()
    port_dict_bindings,switch_details = vtep_obj.get_ovsdb_bindings()
    return  port_dict_bindings,switch_details


if __name__ == '__main__':
    spv = fetch_t1_timestamp_data()
#    print "mysql data", spv
    port_dict_bindings,switch_details=get_ovsdb_data()
#    print "port_dict_bindings" , port_dict_bindings
#    print "switch_details" , switch_details
    vlan_dict(port_dict_bindings)
   









