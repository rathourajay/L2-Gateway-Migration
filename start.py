#!/usr/bin/bash

import sys
from src import db_migration
from src.common import exceptions


if __name__ == '__main__':
    try:
        x = db_migration.MigrationScript()
        x.get_connection_list()
    except Exception as e:
        sys.stderr.write(e.message)
        sys.exit()
        

