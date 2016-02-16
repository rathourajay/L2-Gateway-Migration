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
import config_reader

CONF_FILE="/home/ubuntu/L2-Gateway-Migration/conf/input_data.cfg"

def get_user_token(user_name, password, tenant_name):
        """
        Gets a keystone usertoken using the credentials provided by user
        """

        creds_dict=config_reader.get_config_vals(CONF_FILE)
        service_ip = creds_dict['service_ip']
        os_auth_url = "http://%s:5000/v2.0"  % (service_ip)
        #os_auth_url= "http://10.8.20.51:5000/v2.0"

        url = os_auth_url + '/tokens'
        #log.info("Getting token for user: "
        #         "% s from url: % s" % (user_name, os_auth_url))


        cred_list = creds_dict['cred_list']
        #import pdb
        #pdb.set_trace()
        """To Do: Make a generic method"""

        username = cred_list[0][1]
        password = cred_list[1][1]
        tenant_name = cred_list[2][1]

        
        creds = {
            'auth': {
                'passwordCredentials': {
                    'username': username,
                    'password': password
                    },
                'tenantName': tenant_name
            }
        }

       # import pdb;pdb.set_trace()
        data = json.dumps(creds)
        resp = post_request(url, data=data)
        return resp.json()['access']

def generic_request(method, url, data=None,
                    auth_token=None, nova_cacert=False, stream=False):
    headers = {}
    headers["Content-type"] = "application/json"
    
   # import pdb;pdb.set_trace()
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


