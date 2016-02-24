"""
Created on Feb 2016

@author: gur40998

Description: Main file for L2 Migration

"""

import sys
from src import db_migration
from src.common import exceptions


if __name__ == '__main__':
    try:
        x = db_migration.MigrationScript()
        x.execute_migration()
    except Exception as e:
        sys.stderr.write(e.message)
        sys.exit()
        

