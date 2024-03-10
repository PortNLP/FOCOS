import os
from flask import session
from datetime import datetime, timezone
import mysql.connector as MySQLConnector

# Access environment variables for database connection
db_host = os.environ.get('DB_HOST', 'localhost')
db_user = os.environ.get('DB_USER', 'default_user')
db_password = os.environ.get('DB_PASSWORD', 'default_password')
db_database = os.environ.get('DB_DATABASE', 'default_database')

class User():
    def __init__(self, user_id, password):
        self.id = user_id
        self.password = password

    def is_authenticated(self):
        """
        Returns True if the user is authenticated.
        """
        return verifyPassword(self)

    def is_active(self):
        """
        Returns True if the user is active.
        """
        return True  # You may implement your user activation logic here

    def is_anonymous(self):
        """
        Returns True if the user is anonymous.
        """
        return False  # Since this is a registered user, return False

    def get_id(self):
        """
        Returns the unique identifier for the user.
        """
        return self.id  # Return user ID as a string
    
def verifyPassword(user):
        connection = MySQLConnector.connect(host=db_host,
        user=db_user,
        password=db_password,
        database=db_database)

        cursor = connection.cursor()

        # Check if our database exists
        try:
            fetchQuery = f"SELECT password FROM users where id = %s"
            cursor.execute(fetchQuery, (user.id,) )
            setPassword = cursor.fetchone()[0]
            if(setPassword == user.password):
                return True
            
            return False

        except MySQLConnector.errors.ProgrammingError as e:
            print(e.msg)
        finally:
            cursor.close()
            connection.close()

def get_user(userid):

    connection = MySQLConnector.connect(host=db_host,
    user=db_user,
    password=db_password,
    database=db_database)

    cursor = connection.cursor()

    try:
        fetchQuery = f"SELECT password FROM users where id = %s"
        cursor.execute(fetchQuery, (userid,) )
        setPassword = cursor.fetchone()[0]
        return User(userid,setPassword)
    except MySQLConnector.errors.ProgrammingError as e:
            print(e.msg)
    finally:
            cursor.close()
            connection.close()

    return None

def initUsers():
        
        connection = MySQLConnector.connect(host=db_host,
        user=db_user,
        password=db_password,
        database=db_database)

        cursor = connection.cursor()

        # Check if our database exists
        try:
            cursor.execute("SELECT COUNT(id) FROM users")
            cursor.fetchall() # this is a MySQL oddity
        except MySQLConnector.errors.ProgrammingError as e:
            definition = "CREATE TABLE users (id VARCHAR(50) NOT NULL PRIMARY KEY, password text, last_active datetime)"
            cursor.execute(definition)
            cursor.fetchall() # this is a MySQL oddity
            adminQuery = f"INSERT INTO users (id,password,last_active) values(%s,%s,%s)"
            now = datetime.now(timezone.utc)
            cursor.execute(adminQuery, (db_user,db_password, now))
            cursor.fetchall() # this is a MySQL oddity
        finally:
            connection.commit()
            cursor.close()
            connection.close()

def update_last_active(user,now):
        
        connection = MySQLConnector.connect(host=db_host,
        user=db_user,
        password=db_password,
        database=db_database)

        cursor = connection.cursor()

        # Check if our database exists
        try:
            UpdateQuery = f"update users set last_active = %s where id = %s"
            now = datetime.now(timezone.utc)
            cursor.execute(UpdateQuery, (now, user))
            cursor.fetchall() # this is a MySQL oddity
        except MySQLConnector.errors.ProgrammingError as e:
            raise e
        finally:
            connection.commit()
            cursor.close()
            connection.close()