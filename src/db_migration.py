import requests
import json
import csv
import os
#import logging
#import config

#log = logging.getLogger('baremetal')
ADMIN_DIR = ''
USER_DIR = ''

class MigrationScript(object):

    def __init__(self):
        global USER_DIR
        global ADMIN_DIR
#        self.openstack_obj = openstack_connection.OpenStackConnection(self)
#        self.log = logging.getLogger('baremetal')
        self.cfile = os.getcwd()
        USER_DIR = self.cfile + '/../../data/'
        ADMIN_DIR = self.cfile + '/../../conf/admin'
    
    def get_headers(self):
        auth_token = get_user_token('admin','unset','demo')
        token_id = auth_token['token']['id']
        headers = {
                'User-Agent': 'python-neutronclient',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Auth-Token': token_id,
                }
        print token_id
        
    def get_connection_list(self):
        """
        Getting the list of connections
        """
        list_conn = requests.get('http://10.8.20.51:9696/v2.0/l2-gateway-connections.json', headers=headers)
        connection_list = list_conn.text
        print connection_list

        

    def populate_file(self):
        pass

    

def get_user_token(user_name, password, tenant_name):
        """
        Gets a keystone usertoken using the credentials provided by user
        """
        os_auth_url = 'http://10.8.20.51:5000/v2.0'
        url = os_auth_url + '/tokens'
       # log.info("Getting token for user: "
        #         "% s from url: % s" % (user_name, os_auth_url))
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
'''

if __name__=='__main__':
    try:
        auth_token = get_user_token('admin','unset','demo')
        token_id = auth_token['token']['id']
        headers = {
    		'User-Agent': 'python-neutronclient',
    		'Content-Type': 'application/json',
		'Accept': 'application/json',
		'X-Auth-Token': token_id,
                }
        print token_id
        payload = {"l2_gateway_connection": {"network_id": "d1165e8a-a5d9-4be3-822d-7481572dabbd", "l2_gateway_id": "c6328e84-d80b-43dd-bea2-cc98c4c6fa3d"}}
	"""
	creating connection
	"""
        create_conn = requests.post('http://10.8.20.51:9696/v2.0/l2-gateway-connections.json', data=json.dumps(payload), headers=headers)
        print create_conn.text

        """
	Getting the list of connections
	"""
        list_conn = requests.get('http://10.8.20.51:9696/v2.0/l2-gateway-connections.json', headers=headers)
        connection_list = list_conn.text
        print connection_list
        with open('data.csv', 'wb') as fp:
            a = csv.writer(fp, delimiter=',')
            data = [[connection_list]]
            a.writerows(data)
#fetch network_id and gw_id from data now.
#iterate the data and create new connections.
    except Exception as e:
        print e
'''
