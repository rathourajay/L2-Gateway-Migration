import ConfigParser
import os

#CONF_FILE = "/home/ubuntu/L2-Gateway-Migration/conf/input_data.cfg"

class ConfigReader:

    def __init__(self, conf_file):
        self.conf_file = conf_file
        self.config = ConfigParser.ConfigParser()
        self.config.read(conf_file)

    def get_config_vals(self, *args):
        """TO Do: Use args and kwargs to accept dynamic num of parameters"""

        #creds_list=config.items('OPENSTACK_CREDS')
        service_ip= config.get('default','service_ip')
        conf_dict = {}
        conf_dict['service_ip'] = service_ip
        conf_dict['cred_list'] = creds_list
        return conf_dict

