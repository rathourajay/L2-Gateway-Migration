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
import time
from src.db_migration import MigrationScript
from src.common.database_connection import DB_Connection 
import MySQLdb
from src.common.vtep_add_switch import vtep_command_manager 

def unbind_ls(switch_name_ovsdb,port_name,ovs_vlan_list):
    vtep_obj = vtep_command_manager()
    client = vtep_obj.connect_host('10.8.20.112','root','ubuntu')
    for vlan in ovs_vlan_list:
#        import pdb;pdb.set_trace()
        exec_unbind_cmd = 'cd /home/ubuntu;./vtep-ctl unbind-ls %s %s %s' % (switch_name_ovsdb,port_name,vlan)
        stdin, stdout, stderr = client.exec_command(exec_unbind_cmd)
#    print "Unbinding vlan binding"

def bind_ls(switch_name_ovsdb,port_name,ovs_vlan_list,ls_dict):
    vtep_obj = vtep_command_manager()
    client = vtep_obj.connect_host('10.8.20.112','root','ubuntu')
    for vlan in ovs_vlan_list:
	for key in ls_dict.keys():
	    if vlan ==key:
	        ls_name = ls_dict[key].replace('\n','')
#		import pdb;pdb.set_trace()
	        exec_bind_cmd = 'cd /home/ubuntu;./vtep-ctl bind-ls %s %s %s %s' % (switch_name_ovsdb,port_name.replace('\n',''),vlan,ls_name)
        	stdin, stdout, stderr = client.exec_command(exec_bind_cmd)
		
#    print "Unbinding vlan binding"


def get_ls_name(ls_id,ls_dict):
    for key in ls_dict.keys():
        if ls_id == key.replace('\n','').strip():
            ls_name = ls_dict[key].replace('\n','')
	    return ls_name



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
   # print "spv",spv
   # print "ovsdb data",switch_final
    for switch in spv:
        if switch_final.has_key(switch):
            switch_diff[switch]={}
            switch_diff1[switch]={}
            #if not spv[switch]:
            #    sw_port[switch]=switch_final[switch]
               
            for port in spv[switch]:
                switch_diff[switch][port]=list(set(switch_final[switch][port]) - set(spv[switch][port]))

            for port1 in switch_final[switch]:
#	        import pdb;pdb.set_trace()
                switch_diff1[switch][port1]=list(set(spv[switch][port1]) - set(switch_final[switch][port1]))

    '''
    for ovssw in switch_final:
	if spv.has_key(ovssw):
	    switch_diff1[switch]={}
	        
            for port1 in switch_final[ovssw]:
                switch_diff1[ovssw][port1]=list(set(spv[ovssw][port1]) - set(switch_final[ovssw][port1]))
		
	    sw_port[switch]=list(set(switch_final[switch]) - set(spv[switch]))
    '''
   # print "switch diff1", switch_diff1
 #   import pdb;pdb.set_trace()
    return switch_diff,switch_diff1
            
def add_ucast_ovsdb(mac,ls_name,ip):
    vtep_obj = vtep_command_manager()
    print "ip is ",ip
    client = vtep_obj.connect_host('10.8.20.112','root','ubuntu')
    exec_addls_cmd = 'cd /home/ubuntu;./vtep-ctl add-ucast-remote %s %s %s' % (ls_name,mac,ip)
    stdin, stdout, stderr = client.exec_command(exec_addls_cmd)
    

def del_ucast_ovsdb(mac,ls_name):
    vtep_obj = vtep_command_manager()
    client = vtep_obj.connect_host('10.8.20.112','root','ubuntu')
    exec_addls_cmd = 'cd /home/ubuntu;./vtep-ctl del-ucast-remote %s %s' % (ls_name,mac)
    stdin, stdout, stderr = client.exec_command(exec_addls_cmd)




def get_ls_name_ovsdb(ls_id,ls_ovsdb_data):
    print ls_id
    print ls_ovsdb_data
    for item in ls_ovsdb_data:
	if ls_id in item['uuid']:
            ls_name = item['name'].split(':')[1].replace('\n','').strip()
	    return ls_name

def compare_ucast_data(ucast_mysql_dict,ucast_ovsdb_data,ls_dict,ls_ovsdb_data):
    print "ucast_mysql_dict    " , ucast_mysql_dict
    print "ucast_ovsdb_data    " , ucast_ovsdb_data
    uuid_to_add = []
    uuid_to_del = []
    #flag = False
    #flag1 = False
    for uuid in ucast_mysql_dict:
#	import pdb;pdb.set_trace()
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
    print "uuid to add   ",  uuid_to_add
    print "uuid to del   ", uuid_to_del
    import pdb;pdb.set_trace()
    return uuid_to_add,uuid_to_del,ls_dict,ls_ovsdb_data


def switch_dict(switch_details,port_vlan,prt_id_name_dict,ls_key_name_dict,port_dict_bindings,uuid_to_add, uuid_to_del,ls_dict,ls_ovsdb_data):
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
    unbind_vlan_dict,bind_vlan_dict = compare(spv,switch_final)
    
    for sw1 in bind_vlan_dict:
        for port in bind_vlan_dict[sw1]:
#	    import pdb;pdb.set_trace()
	    port_name = prt_id_name_dict[port]

	    if bind_vlan_dict[sw1][port]:
                if len(bind_vlan_dict[sw1][port][0])>0:
                    vlan_lst =  bind_vlan_dict[sw1][port]
                    print "bind data" , sw1,port_name,vlan_lst,ls_key_name_dict
                    bind_ls(sw1,port_name,vlan_lst,ls_key_name_dict)
    
    if uuid_to_add:
	for uuid in uuid_to_add:
	    for item in ucast_mysql_dict:
		if uuid in item:
		    mac = ucast_mysql_dict[item][0]
		    ls_id = ucast_mysql_dict[item][1].replace('\n','').strip()
		    ls_name = get_ls_name(ls_id,ls_dict)
		    ip = ucast_mysql_dict[item][2].replace('\n','').strip()
		    #print "print ip",ip	
		    add_ucast_ovsdb(mac,ls_name,ip)

    if uuid_to_del:
        for uuid in uuid_to_del:
            for item in ucast_ovsdb_data:
                #import pdb;pdb.set_trace()
                if uuid in item['uuid']: 
                    mac = item['mac'].split(': ')[1].replace('\n','').strip()
                    ls_id = item['logical_switch'].split(':')[1].replace('\n','').strip()
                    ls_name = get_ls_name_ovsdb(ls_id,ls_ovsdb_data)
		    del_ucast_ovsdb(mac,ls_name)


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


def vlan_dict(port_dict_bindings,prt_id_name_dict,ls_key_name_dict,uuid_to_add, uuid_to_del,ls_dict,ls_ovsdb_data):
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
    switch_dict(switch_details,port_vlan,prt_id_name_dict,ls_key_name_dict,port_dict_bindings,uuid_to_add, uuid_to_del,ls_dict,ls_ovsdb_data)


def fetch_t1_timestamp_data():
    db_user_id = config.CONF.DATABASE_CRED.db_user_id
    db_pwd = config.CONF.DATABASE_CRED.db_pwd
    db_name = config.CONF.DATABASE_CRED.db_name
    db_obj = DB_Connection()
    client = db_obj.connect_host()

    switch_query =  'sudo mysql -e "select physical_switches.uuid , physical_switches.name from physical_switches;" -u %s -p%s %s' % (db_user_id,db_pwd,db_name)
    sw_port_query =  'sudo mysql -e "select physical_switches.uuid , physical_switches.name , physical_ports.uuid, physical_ports.name from physical_switches join physical_ports ON physical_switches.uuid = physical_ports.physical_switch_id;"  -u %s -p%s %s' % (db_user_id,db_pwd,db_name)
    
    sw_port_vlan_query = 'sudo mysql -e "select physical_switches.uuid , physical_switches.name , physical_ports.uuid, physical_ports.name, vlan_bindings.vlan from physical_switches join physical_ports ON physical_switches.uuid = physical_ports.physical_switch_id JOIN vlan_bindings ON physical_ports.uuid = vlan_bindings.port_uuid;" -u %s -p%s %s' % (db_user_id,db_pwd,db_name)
   
    ucast_query = 'sudo mysql -e "select ucast_macs_remotes.uuid,ucast_macs_remotes.mac,ucast_macs_remotes.logical_switch_id, ucast_macs_remotes.ip_address from ucast_macs_remotes;" -u %s -p%s %s' % (db_user_id,db_pwd,db_name)
 
    ls_key_name_dict = {}
    ls_id_dict = {}
    ls_data_query = 'sudo mysql -e "select logical_switches.key ,logical_switches.name, logical_switches.uuid from logical_switches;"  -u %s -p%s %s' % (db_user_id,db_pwd,db_name)
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
	 #   print port_name
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
            port_name = str(line.split('\t')[3])
            prt_id_name_dict[port_id] = port_name
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

    return spv,prt_id_name_dict,ls_key_name_dict,ucast_data_dict,ls_id_dict

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
    spv,prt_id_name_dict,ls_key_name_dict,ucast_mysql_dict,ls_id_dict = fetch_t1_timestamp_data()

    #port_dict_bindings,switch_details=get_ovsdb_data()
    #vlan_dict(port_dict_bindings,prt_id_name_dict,ls_key_name_dict)

    vtep_obj = vtep_command_manager()
    ucast_ovsdb_data = vtep_obj.get_ucast_data()   
    ls_ovsdb_data = vtep_obj.get_ls_data()
    uuid_to_add, uuid_to_del,ls_dict,ls_ovsdb_data = compare_ucast_data(ucast_mysql_dict,ucast_ovsdb_data,ls_id_dict,ls_ovsdb_data)

    port_dict_bindings,switch_details=get_ovsdb_data()
    vlan_dict(port_dict_bindings,prt_id_name_dict,ls_key_name_dict,uuid_to_add, uuid_to_del,ls_dict,ls_ovsdb_data)








