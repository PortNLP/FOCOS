import os
import shutil
from datetime import datetime, timezone, timedelta
import mysql.connector as MySQLConnector

# Access environment variables for database connection
db_host = os.environ.get('DB_HOST', 'localhost')
db_user = os.environ.get('DB_USER', 'default_user')
db_password = os.environ.get('DB_PASSWORD', 'default_password')
db_database = os.environ.get('DB_DATABASE', 'default_database')

if __name__ == '__main__':

    print("Purger started .....")

    connection = MySQLConnector.connect(host=db_host,
        user=db_user,
        password=db_password,
        database=db_database)

    cursor = connection.cursor()

    # Check if our database exists
    try:
        timelimit = datetime.now(timezone.utc) - timedelta(minutes=30)
        cursor.execute(f"SELECT id FROM users where last_active < %s",(timelimit,))
        users = cursor.fetchall() # this is a MySQL oddity
        for user in users:
            username = user[0]
            path = os.path.join("/app/temp/",username)

            if os.path.isdir(path):
                print("purging directory at path ", path)
                shutil.rmtree(path)

    except MySQLConnector.errors.ProgrammingError as e:
        print("Something is wrong with the purger")
    finally:
        print("Purger ended")
        connection.commit()
        cursor.close()
        connection.close()