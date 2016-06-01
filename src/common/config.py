"""
Created on Feb 2016

@author: gur40998

Description: Config file for L2 Migration

"""
from oslo_config import cfg
import os

def register_opt_group(conf, opt_group, options):
    conf.register_group(opt_group)
    for opt in options:
        conf.register_opt(opt, group=opt_group.name)

default_group = cfg.OptGroup(name='default',
                             title="Default Configuration Options")

DefaultGroup = [
    cfg.BoolOpt('debug',
                default=False,
                help="Print debugging output")]



opt_mysql_credential_group = cfg.OptGroup(
    name='DATABASE_CRED',
    title='mysql credentials')
mysql_credential_opts = [
    cfg.StrOpt('host_ip',
               default='localhost',
               help=('Host ip address to connect to mysql')),
    cfg.StrOpt('host_uname',
               default='root',
               help=('Username to connect to Host')),
    cfg.StrOpt('host_pwd',
               default='password',
               help=('Password to connect to host')),
    cfg.StrOpt('db_user_id',
               default='db_user_id',
               help=('Database user id')),
    cfg.StrOpt('db_pwd',
               default='db_pwd',
               help=('database password')),
    cfg.StrOpt('db_name',
               default='db_name',
               help=('database password'))]


opt_openstack__credential_group = cfg.OptGroup(
    name='KEYSTONE_CREDS',
    title='keystone credentials')
openstack_credential_opts = [
    cfg.StrOpt('username',
               default='admin',
               help=('Openstack username')),
    cfg.StrOpt('password',
               default='admin',
               help=('password KEYSTONE_CREDS')),
    cfg.StrOpt('log_file',
               default='log_file',
               help=('Log_file path')),
    cfg.StrOpt('tenant_name',
               default='tenant',
               help=('tenant name'))
]

opt_openstack__credential_group = cfg.OptGroup(
    name='KEYSTONE_CREDS',
    title='keystone credentials')
openstack_credential_opts = [
    cfg.StrOpt('username',
               default='admin',
               help=('Openstack username')),
    cfg.StrOpt('password',
               default='admin',
               help=('password KEYSTONE_CREDS')),
    cfg.StrOpt('log_file',
               default='log_file',
               help=('Log_file path')),
    cfg.StrOpt('tenant_name',
               default='tenant',
               help=('tenant name'))
]

opt_ovsdb_host__credential_group = cfg.OptGroup(
    name='OVSDB_HOST_CREDS',
    title='ovs credentials')
ovsdb_host_credential_opts = [
    cfg.StrOpt('username',
               default='root',
               help=('ovsdb machine username')),
    cfg.StrOpt('password',
               default='ubuntu',
               help=('ovsdb machine password')),
    cfg.StrOpt('log_file',
               default='log_file',
               help=('Log_file path')),
    cfg.StrOpt('host_ip',
               default='10.8.20.112',
               help=('ovsdb machine ip')),
]

def register_opts():
    register_opt_group(
        cfg.CONF, opt_mysql_credential_group, mysql_credential_opts)
    register_opt_group(
        cfg.CONF, opt_openstack__credential_group, openstack_credential_opts)
    register_opt_group(
        cfg.CONF, opt_ovsdb_host__credential_group, ovsdb_host_credential_opts)
    register_opt_group(cfg.CONF, default_group, DefaultGroup)
    

def get_config():
    conf_file = '/etc/input_data.conf'
    cfg.CONF(default_config_files=[conf_file])
    #cfg.CONF(default_config_files=['/home/ubuntu/L2-Gateway-Migration/conf/input_data.conf'])
    register_opts()
    return cfg.CONF


CONF = get_config()

