import ConfigParser
import os, sys
import exceptions
import socket
import re

def get_config_vals(conf_file):

    """
    TO Do: Use args and kwargs to accept dynamic num of parameters,
    Apply validation if config file is empty
    """
   
    config = ConfigParser.ConfigParser()
    config.read(conf_file)
    try:
        creds_list=config.items('OPENSTACK_CREDS')
        service_ip= config.get('default','service_ip')
        socket.inet_aton(service_ip)
        ip_pat = re.findall('\d+\.\d+\.\d+\.\d+$',service_ip)
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
    conf_dict['service_ip'] = service_ip
    conf_dict['cred_list'] = creds_list

    return conf_dict 



    
