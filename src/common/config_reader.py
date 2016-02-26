import ConfigParser
import os, sys
import exceptions
import socket
import re

def get_config_vals(conf_file):

    """
    Apply validation if config file is empty
    This file is not being used,integrated with db_migration.py
    """
   
    config = ConfigParser.ConfigParser()
    config.read(conf_file)
    try:
        #sys.stdout.debug("Reading credentials from conf file..")
        creds_list=config.items('OPENSTACK_CREDS')
        controller_ip= config.get('default','controller_ip')
        socket.inet_aton(controller_ip)
        ip_pat = re.findall('\d+\.\d+\.\d+\.\d+$',controller_ip)
        if not ip_pat:
            raise exceptions.InvalidIpAddress('IP validation failed') 

    except(ConfigParser.NoOptionError,ConfigParser.NoSectionError) as e:
        sys.stderr.write(e.message+'in provided config file'+'\n')
        sys.exit()
    
    except exceptions.InvalidIpAddress as e:
        print "inside config reader"
        sys.stderr.write(e._error_string+'\n')
        sys.exit()
    except socket.error as e:
        sys.stderr.write("IPV4 address validation failed" + '\n')
        sys.exit()
    except IOError as e:
        sys.stderr.write("Invalid config file format" + '\n')
        sys.exit()
 
    conf_dict = {}
    conf_dict['controller_ip'] = controller_ip
    conf_dict['cred_list'] = creds_list

    return conf_dict 



    
