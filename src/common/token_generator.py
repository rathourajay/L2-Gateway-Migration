"""
Created on March 2016

@author:

Description: Exception file for L2 Migration

"""

import requests
import json
import logging
import config
import csv 
import ConfigParser, os
import sys
log = logging.getLogger('l2_gateway')


def get_user_token(user_name, password, tenant_name,host_ip):
        """
        Gets a keystone usertoken using the credentials provided by user
        """
        os_auth_url = "http://%s:5000/v2.0"  % (host_ip)

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
        log.info("Post request_response =="
                 "% s " % (resp))
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
    log.info("In function generic_request")
    if resp.status_code in [401]:
        resp_body = resp.json()
    if resp.status_code in [403]:
        resp_body = resp.json()

    elif resp.status_code not in [200, 201, 203, 204]:
        print "Can't able to make connection"
        log.info("Can't able to make connection")
    return resp

"""
TO DO: get_request method is not being used, later on delete
"""
def get_request(url, auth_token, nova_cacert=False, stream=False):
    return generic_request(requests.get, url, auth_token=auth_token,
                           nova_cacert=nova_cacert, stream=stream)


def post_request(url, data, auth_token=None):
    return generic_request(requests.post, url, data, auth_token)


