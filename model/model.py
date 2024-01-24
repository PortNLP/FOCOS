from model.fcm import run_inference, get_connections
import sqlite3
import os
import mysql.connector as MySQLConnector
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from datetime import date
DB_FILE = 'focos.db'    # file for our Database
FCM_MODEL = "V1"
db = SQLAlchemy()

# Access environment variables for database connection
db_host = os.environ.get('DB_HOST', 'localhost')
db_user = os.environ.get('DB_USER', 'default_user')
db_password = os.environ.get('DB_PASSWORD', 'default_password')
db_database = os.environ.get('DB_DATABASE', 'default_database')

class model():

    def __init__(self,app):
        print("Created model")

        # Dict {fcm_principle_name : output_principle_name}
        self.principle_dict = {
            "Deference to Expertise" :      "DEFERENCE TO EXPERTISE",
            "Commitment to Resilience" :    "COMMITMENT TO RESILIENCE",
            "Sensitivity to Operations" :   "SENSITIVITY TO OPERATION",
            "Reluctance to Simplify " :     "RELUCTANCE TO SIMPLIFY",
            "Preoccupation With Failure" :  "PREOCCUPATION WITH FAILURE"
        }

        # Dict {slider_name : intervention_name}
        self.intervention_dict = {
            "AuthoritySlider" :       "Stop-Work-Authority",
            "IncidentsSlider" :       "Reporting of Near Misses and Safety-Critical Events",
            "RespectSlider" :         "Fostering Social Ties and Mutual Respect",
            "AccountabilitySlider" :  "Fostering a Sense of Personal Accountability for Safety on All Levels",
            "HuddleSlider" :          "Implementing Safety Huddles",
            "ExerciseSlider" :        "Practicing Tabletop Exercises",
            "DebriefingsSlider" :     "Practicing Post-Event Debriefings",
            "DrillsSlider" :          "Practicing Emergency Drills",
            "MotivationSlider" :      "Institutionalizing Prosocial Motivation",
            "AmbivalenceSlider" :     "Institutionalizing Emotional Ambivalence",
            "DriftSlider" :           "Managing Reliability Drift",
            "MindfulnessSlider" :     "Practicing Individual Mindfulness",
            "LearningSlider" :        "Adopting Just-In-Time Learning"
        }
        self.intervention_names = [k for (k,v) in self.intervention_dict.items()]

        # Access environment variables for database connection
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_user = os.environ.get('DB_USER', 'default_user')
        db_password = os.environ.get('DB_PASSWORD', 'default_password')
        db_database = os.environ.get('DB_DATABASE', 'default_database')

        connection = MySQLConnector.connect(host=db_host,
        user=db_user,
        password=db_password,
        database=db_database)

        cursor = connection.cursor()

        # Check if our database exists
        try:
            cursor.execute("SELECT COUNT(name) FROM strategies")
        except MySQLConnector.errors.ProgrammingError as e:
            definition = "CREATE TABLE strategies (model VARCHAR(50), day text, name VARCHAR(50) NOT NULL PRIMARY KEY, description text, function_type VARCHAR(10) DEFAULT ('tanh')"
            for intervention in self.intervention_names:
                definition += ", " + intervention + " INTEGER"
            definition = definition + ")"
            cursor.execute(definition)
            connection.commit()

        cursor.fetchall() # this is a MySQL oddity
        cursor.close()
        connection.close()

        # Check if our MySQL database exists
        
        """
        try:
            with app.app_context():
                db.session.execute(text("SELECT COUNT(name) FROM strategies"))
        except:
            with app.app_context():
                definition = '''CREATE TABLE strategies (model text, day text, name varchar(50) NOT NULL PRIMARY KEY, description text, 
                                   function_type text DEFAULT ('tanh') '''
                for intervention in self.intervention_names:
                    definition += ", " + intervention + " INTEGER"
                definition = definition + ")"
                db.session.execute(text(definition))
                db.session.commit()
        """
        

    def get_results(self, intervention_sliders, modified_connections={}, function_type = "tanh"):
        """
        Gets the 5 degrees to which the HRO principles change
         in response to the latest strategy. Also returns the principle names
        :param intervention_sliders: Dict {slider_name : value}
        :param modified_connections: Dict {practice : connections}
        :return: List of Floats, List of Strings
        """

        output_principle_names = []
        fcm_principle_names = []
        for key, val in self.principle_dict.items():
            output_principle_names.append(key)
            fcm_principle_names.append(val)


        if not intervention_sliders:  # no intervention
            effects = [0, 0, 0, 0, 0]
        else:
            interventions = {}
            for key, val in intervention_sliders.items():
                name = self.intervention_dict[key]
                value = float(val) * 0.01   # Convert from percent
                interventions.update({name : value})
            print(interventions)

            # Get results for the latest strategy
            effects = run_inference(interventions, fcm_principle_names, modified_connections, function_type = function_type)

        return effects, output_principle_names

    def get_practice_connections(self, practice_slider_name):
        """
        Get the connections for a certain practice      
        :param practice_slider_name: String
        :return: Dict {practice_name : value}
        """
        practice = self.intervention_dict[practice_slider_name]
        return get_connections(practice)

    def save_strategy(self, intervention_sliders, name, description, function_type = "tanh"):
        """
        Save Current Strategy
        :param intervention_sliders: Dict {slider_name : value}
        :param name: String
        :param description: String
        :return: none
        """

        intervention_values = [intervention_sliders[k] for k in self.intervention_names]
        day = date.today()
        model = FCM_MODEL
        connection = get_db()
        cursor = connection.cursor(dictionary=True)

        columns_str = ", ".join(self.intervention_names)
        length = len(self.intervention_names)
        values = ", ".join(["%s" for _ in range(length)])
        sql = f"INSERT INTO STRATEGIES (model,day,name,description,function_type,{columns_str}) VALUES (%s, %s, %s, %s, %s, {values})"

        # Check if our database exists
        try:
            cursor.execute(sql, (model, day, name, description, function_type) + tuple(intervention_values))
        except MySQLConnector.errors.ProgrammingError as e:
            print(e)
            return False
        finally:
            connection.commit()
            cursor.fetchall() # this is a MySQL oddity
            cursor.close()
            connection.close()
        
        return True

        """
        intervention_values = [intervention_sliders[k] for k in self.intervention_names]
        day = date.today()
        model = FCM_MODEL
        connection = get_db()
        cursor = connection.cursor()
        sql = "INSERT INTO strategies VALUES (?,?,?,?,?" + ",?"*len(self.intervention_names) + ")"


        try:
            print(tuple(intervention_values))
            UserModel = DbModel(name=name,day=day,description=description,function_type=function_type,
                                intervention_values=tuple(intervention_values))
        except e:
            print(e)

        try:
            cursor.execute(sql, (model, day, name, description, function_type) + tuple(intervention_values))
        except sqlite3.IntegrityError as e:
            print(e)
            return False
        #cursor.execute("SELECT * FROM strategies")
        #print(cursor.fetchall())
        connection.commit()
        cursor.close()
        return True
        """

    def select_all(self):
        """
        Select all rows
        :return: List of Dicts
        """
        
        try:
            connection = get_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM strategies")
        finally:
            rows = cursor.fetchall()
            connection.commit()
            #print(rows)
            cursor.close()
            connection.close()


        return rows

    def select_strategy(self, name):
        """
        Select a certain strategy based on name
        :param name: String
        :return: Dict
        """

        try:
            connection = get_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute('''SELECT * FROM strategies WHERE name = %s''', tuple([name]))
            row = cursor.fetchall()[0]
        finally:
            #print(row)
            cursor.close()
            connection.close()

        return row

    def update_description(self, name, new_name, description):
        """
        Update a certain strategy based on name
        :param name: String
        :return: Dict
        """
        try:
                
            connection = get_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute('''UPDATE strategies SET description = %s WHERE name = %s''', (description, name,))
            cursor.execute('''SELECT * FROM strategies WHERE name = %s''', (name,))
            row = cursor.fetchall()[0]
            #print(row)
        finally:    
            connection.commit()
            cursor.close()
            connection.close()

        return row

    def delete_strategy(self, name):
        """
        Delete a certain strategy based on name
        :param name: String
        :return: None
        """
        try:
            connection = get_db()
            cursor = connection.cursor()
            cursor.execute('''DELETE FROM strategies WHERE name = %s''', (name,))
        finally:
            connection.commit()
            cursor.close()
            connection.close()

        return True

def get_db():
    connection = None
    try:
        connection = MySQLConnector.connect(host=db_host,
        user=db_user,
        password=db_password,
        database=db_database)
    except Exception as e:
        print(e)
    return connection

# results from the database are returned as dictionaries instead of tuples
def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))