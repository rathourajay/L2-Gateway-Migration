import ConfigParser
import os

#CONF_FILE = "/home/ubuntu/L2-Gateway-Migration/conf/input_data.cfg"


def get_config_vals(conf_file):
    """TO Do: Use args and kwargs to accept dynamic num of parameters"""

    config = ConfigParser.ConfigParser()
    config.read(conf_file)
    creds_list=config.items('OPENSTACK_CREDS')
    service_ip= config.get('default','service_ip')
    conf_dict = {}
    conf_dict['service_ip'] = service_ip
    conf_dict['cred_list'] = creds_list
    return conf_dict 



    
