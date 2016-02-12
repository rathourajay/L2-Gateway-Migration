import db_migration

if __name__ == '__main__':
    try:
        x = db_migration.MigrationScript()
        x.get_connection_list()
    except Exception as e:
        print e
