import ConfigParser
import os

CONF_FILE = "params.cfg"

def get_config_vals(conf_file):

    config = ConfigParser.ConfigParser()
    #imy_file = (os.path.join(os.getcwd(),'parser.cfg'))
    config.read(conf_file)
    service_ip= config.get('default','service_ip')
    print service_ip
#    option = None
#   try:
#        service_ip=config.items('default')
#        print service_ip
#    except ConfigParser.NoOptionError as e:
#        return option
#    return option


service_ip = get_config_vals(CONF_FILE)
