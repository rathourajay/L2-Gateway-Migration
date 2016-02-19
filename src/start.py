import db_migration
import sys
from common import exceptions
if __name__ == '__main__':
    try:
        x = db_migration.MigrationScript()
        x.get_connection_list()
    except exceptions.InvalidIpAddress as e:
        sys.stdout.write(e._error_string+'\n')
        sys.exit() 
        

