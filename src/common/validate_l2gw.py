# (C) Copyright 2016 Hewlett Packard Enterprise Development LP

import config
import logging
import migration_exceptions
import socket
import sys
import re
log = logging.getLogger('l2_gateway')

class L2gw_Validation():

    def __init__(self):
        self.host_ip = config.CONF.DATABASE_CRED.host_ip
#        self.log = logging.getLogger('l2gw')

    def validate_neutrondb_host(self):
        try:
            log.info("validating NeutronDB host_ip %s\n" % (self.host_ip))
            socket.inet_aton(self.host_ip)
            ip_pat = re.findall('\d+\.\d+\.\d+\.\d+$', self.host_ip)
            if not ip_pat:
                raise migration_exceptions.ValueError(
                    'IP validation failed')
        except Exception as e:
            log.error("Invalid NeutronDB host ip %s \n" % (self.host_ip))
            sys.stdout.write("Invalid NeutronDB host ip "
                             "%s \n" % (self.host_ip))
            raise Exception

# Below functions to be modifies ad per OVSDB migration.

    def validate_ovsdb_param(self, neutrondb_identifiers, ovsdb_identifiers):
        '''
        Validation of l2gw parameters.
        '''
        ovs_identifier_list = []
        ovs_ip_list = []
        for item in ovsdb_identifiers:
            ovs_ip_list.append(str(item.split(':')[1].strip()))
            ovs_identifier_list.append(str(item.split(':')[0].strip()))

        try:
            for ovsdb_host_ip in ovs_ip_list:
                self.log.info("validating OVSDB host_ip %s\n" %
                              (ovsdb_host_ip))
                socket.inet_aton(ovsdb_host_ip)
                ip_pat = re.findall('\d+\.\d+\.\d+\.\d+$', ovsdb_host_ip)
                if not ip_pat:
                    raise l2gw_postrecovery_exception.IPError(
                        'OVSDB host IP validation failed')
        except l2gw_postrecovery_exception.IPError as e:
            self.log.error("Invalid OVSDB host ip %s \n" % (ovsdb_host_ip))
            sys.stdout.write("Invalid OVSDB host ip %s \n" % (ovsdb_host_ip))
            raise Exception

        try:
            for identifier in neutrondb_identifiers:
                self.log.info("validating OVSDB identifier %s "
                              "in conf file\n" % (identifier))
                sys.stdout.write("validating OVSDB identifier %s "
                                 "in conf file\n" % (identifier))
                if identifier not in ovs_identifier_list:
                    raise l2gw_postrecovery_exception.IdentifierError(
                        "validating OVSDB identifier %s "
                        "in conf file\n" % (identifier))
        except l2gw_postrecovery_exception.IdentifierError as e:
            self.log.error("Ovsdb identifier %s not present "
                           "in conf file\n" % (identifier))
            sys.stdout.write("Ovsdb identifier %s not present "
                             "in conf file\n" % (identifier))
            raise Exception
