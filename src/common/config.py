from oslo_config import cfg

def register_opt_group(conf, opt_group, options):
    conf.register_group(opt_group)
    for opt in options:
        conf.register_opt(opt, group=opt_group.name)

default_group = cfg.OptGroup(name='DEFAULT',
                             title="Default Configuration Options")

DefaultGroup = [
    cfg.BoolOpt('debug',
                default=False,
                help="Print debugging output"),
    cfg.StrOpt('service_ip',
               default='service_ip',
               help="service ip ie cmc ip")]




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
    name='OPENSTACK_CREDS',
    title='openstack credentials')
openstack_credential_opts = [
    cfg.StrOpt('username',
               default='admin',
               help=('Openstack username')),
    cfg.StrOpt('password',
               default='admin',
               help=('password OPENSTACK_CREDS')),
    cfg.StrOpt('log_file',
               default='log_file',
               help=('Log_file path')),
    cfg.StrOpt('tenant_name',
               default='tenant',
               help=('tenant name'))
]

def register_opts():
    register_opt_group(
        cfg.CONF, opt_mysql_credential_group, mysql_credential_opts)
    register_opt_group(
        cfg.CONF, opt_openstack__credential_group, openstack_credential_opts)
    register_opt_group(cfg.CONF, default_group, DefaultGroup)
    

def get_config():
    cfg.CONF(default_config_files=['/home/ubuntu/L2-Gateway-Migration/conf/input_data.conf'])
    register_opts()
    return cfg.CONF


CONF = get_config()

