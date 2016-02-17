import codecs
import csv
import paramiko
import json
import config

PATH ='/home/ubuntu/L2-Gateway-Migration/data/'
class db_connection():

    def __init__(self):
        self.host_ip = config.CONF.DATABASE_CRED.host_ip
        self.host_uname = config.CONF.DATABASE_CRED.host_uname
        self.host_pwd = config.CONF.DATABASE_CRED.host_pwd
        self.db_user_id = config.CONF.DATABASE_CRED.db_user_id
        self.db_pwd = config.CONF.DATABASE_CRED.db_pwd
        self.db_name = config.CONF.DATABASE_CRED.db_name

    def connect_host(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.host_ip, username=self.host_uname, password=self.host_pwd)
        return client

    def read_connection_uuid(self):
        #import pdb;pdb.set_trace()
        data_file = PATH + 'data_file.csv' 
        con_ptr = self.connect_host()
        #with codecs.open(data_file, 'r', encoding='utf8') as fd:
        arr = []
        with open(data_file, 'r') as fd:
            reader =  csv.reader(fd, delimiter='\t')
            for line in reader:
                arr.append(line[0])
            
        for item in arr[1:]:
            print item
            self.execute_query(con_ptr,item)
        #return uuid_con

    def execute_query(self,client,uuid_con):
        #import pdb;pdb.set_trace()
        #query = 'sudo mysql -e "select * from l2gatewayconnections" -u neutron -p7342274ae48f99a6262b3653496a02ccb9398d07 ovs_neutron'
        query = 'sudo mysql -e "delete from l2gatewayconnections where id = \'%s\'" -u %s -p%s %s' % (uuid_con,self.db_user_id,self.db_pwd,self.db_name)
        print query
        stdin, stdout, stderr = client.exec_command(query)
        for line in stdout:
            print line.strip('\n')
'''
if __name__ == '__main__':
    db_obj=database_connection()
    print "object created"
    #get_ptr=db_obj.connect_host()
    print "pointer retuned"
    uuid_con = 'aditya_nandan'
    print "executing query"
    #db_obj.execute_query(get_ptr,uuid_con)
    print "executed query"
   
    db_obj.read_connection_uuid()
    
    print "read file and get data"

'''        
