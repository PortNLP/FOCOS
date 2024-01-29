import os
from flask import session
import mysql.connector as MySQLConnector

# Access environment variables for database connection
db_host = os.environ.get('DB_HOST', 'localhost')
db_user = os.environ.get('DB_USER', 'default_user')
db_password = os.environ.get('DB_PASSWORD', 'default_password')
db_database = os.environ.get('DB_DATABASE', 'default_database')

class User():
    def __init__(self, user_id):
        self.id = user_id

    def is_authenticated(self):
        """
        Returns True if the user is authenticated.
        """
        return True  # You may implement your authentication logic here

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
    
def get_user(userid):
    return User(userid)

def initUsers():
        
        connection = MySQLConnector.connect(host=db_host,
        user=db_user,
        password=db_password,
        database=db_database)

        cursor = connection.cursor()

        # Check if our database exists
        try:
            cursor.execute("SELECT COUNT(id) FROM users")
        except MySQLConnector.errors.ProgrammingError as e:
            definition = "CREATE TABLE users (id VARCHAR(50) NOT NULL PRIMARY KEY, password text)"
            cursor.execute(definition)
            connection.commit()

            adminQuery = f"INSERT INTO users (id,password) values(%s,%s)"
            cursor.execute(adminQuery, (db_user,db_password))
            connection.commit()

        cursor.fetchall() # this is a MySQL oddity
        cursor.close()
        connection.close()