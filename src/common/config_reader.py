import ConfigParser
import os
import exceptions
#CONF_FILE = "/home/ubuntu/L2-Gateway-Migration/conf/input_data.cfg"
import re

def get_config_vals(conf_file):
    """TO Do: Use args and kwargs to accept dynamic num of parameters"""
   
    config = ConfigParser.ConfigParser()
    config.read(conf_file)
    creds_list=config.items('OPENSTACK_CREDS')
    service_ip= config.get('default','service_ip')
    conf_dict = {}
    conf_dict['service_ip'] = service_ip
    ip_pat = re.findall('\d+\.\d+\.\d+\.\d+$',service_ip)
    if not ip_pat:
        raise exceptions.InvalidIpAddress('IP validation failed') 
    conf_dict['cred_list'] = creds_list
    return conf_dict 



    
