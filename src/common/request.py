'''
Created on Dec 10, 2015

@author: Aricent
'''
import requests
import json
import logging
import config
import csv 
import ConfigParser, os
import pdb;pdb.set_trace()
#log = logging.getLogger('baremetal')
config =  ConfigParser.ConfigParser()
cfile=os.getcwd()
USER_DIR = cfile + '/../../conf/db_conf'
#config.read('/home/ubuntu/L2_GW_Migration/conf/db_conf')
config.read(USER_DIR)
server_ip =  config.get('SOURCE_IP', 'source_ip', 0)
print server_ip


def get_user_token(user_name, password, tenant_name):
        """
        Gets a keystone usertoken using the credentials provided by user
        """
#        os_auth_url = config.CONF.openstack_credential.os_auth_url
        config =  ConfigParser.ConfigParser()
        cfile=os.getcwd()
        USER_DIR = self.cfile + '/../../conf/db_conf.conf'
        config.read(USER_DIR)
        server_ip =  config.get('SOURCE_IP', 'source_ip', 0)
#        ovsdb_ips =  config.get(source_ip)
        import pdb;pdb.set_trace()
        print server_ip
        url = os_auth_url + '/tokens'
        log.info("Getting token for user: "
                 "% s from url: % s" % (user_name, os_auth_url))
        creds = {
            'auth': {
                'passwordCredentials': {
                    'username': user_name,
                    'password': password
                    },
                'tenantName': tenant_name
            }
        }

        data = json.dumps(creds)
        resp = post_request(url, data=data)
        return resp.json()['access']

def generic_request(method, url, data=None,
                    auth_token=None, nova_cacert=False, stream=False):
    headers = {}
    headers["Content-type"] = "application/json"
    if auth_token:
        token = auth_token['token']
        headers["X-Auth-Token"] = token['id']
    resp = method(url, headers=headers, data=data, verify=nova_cacert,
                  stream=stream)

    if resp.status_code in [401]:
        resp_body = resp.json()
    if resp.status_code in [403]:
        resp_body = resp.json()

    elif resp.status_code not in [200, 201, 203, 204]:
        print "Can't able to make connection"
    return resp


def get_request(url, auth_token, nova_cacert=False, stream=False):
    return generic_request(requests.get, url, auth_token=auth_token,
                           nova_cacert=nova_cacert, stream=stream)


def post_request(url, data, auth_token=None):
    return generic_request(requests.post, url, data, auth_token)


