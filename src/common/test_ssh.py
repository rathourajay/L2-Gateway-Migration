"""
import paramiko
l_password = "ubuntu"
l_host = "10.8.20.110"
l_user = "ubuntu"
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(l_host, username=l_user, password=l_password)    
transport = ssh.get_transport()
session = transport.open_session()
session.set_combine_stderr(True)
session.get_pty()
import pdb;pdb.set_trace()
#for testing purposes we want to force sudo to always to ask for password. because of that we use "-k" key
stdout = session.exec_command("sudo ./vtep-ctl list-ps")
print stdout.readlines()
"""
import paramiko
import getpass
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.8.20.110',username='root',password='ubuntu')
stdin, stdout, stderr = ssh.exec_command('ls')
import pdb;pdb.set_trace()
print stdout.readlines()
