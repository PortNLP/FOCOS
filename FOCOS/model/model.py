from model.fcm import run_inference, run_strategy_inference
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

    def __init__(self):
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
            definition = "CREATE TABLE strategies (model VARCHAR(50), id VARCHAR(50), day text, name VARCHAR(50) NOT NULL, description text, function_type VARCHAR(10) DEFAULT ('tanh'), FILE MEDIUMBLOB DEFAULT NULL"
            for intervention in self.intervention_names:
                definition += ", " + intervention + " INTEGER"
            definition = definition + " ,FOREIGN KEY (id) REFERENCES users(id), PRIMARY KEY (id,name))"
            cursor.execute(definition)
            connection.commit()

        cursor.fetchall() # this is a MySQL oddity
        cursor.close()
        connection.close()

    def get_strategy_results(self, strategy_name, id, intervention_sliders, modified_connections={}, function_type = "tanh"):
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

            weights = get_weights(strategy_name,id)['file']

            # Get results for the latest strategy
            effects = run_strategy_inference(interventions, fcm_principle_names, weights, modified_connections, function_type = function_type)

        return effects, output_principle_names

    def get_results(self, intervention_sliders, modified_connections={}, function_type = "tanh", file_name = None):
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
            effects = run_inference(interventions, fcm_principle_names, modified_connections, function_type = function_type, file_name = file_name)

        return effects, output_principle_names

    def save_strategy(self, intervention_sliders, name, description, userid, function_type = "tanh",file_name = None):
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

        if file_name:
            file = open(file_name,"rb").read()
        else:
            file = None # explicit setting to NULL 

        columns_str = ", ".join(self.intervention_names)
        length = len(self.intervention_names)
        values = ", ".join(["%s" for _ in range(length)])
        sql = f"INSERT INTO STRATEGIES (model,id,day,name,description,function_type,file,{columns_str}) VALUES (%s, %s, %s, %s, %s, %s, %s, {values})"

        # Check if our database exists
        try:
            cursor.execute(sql, (model, userid, day, name, description, function_type,file) + tuple(intervention_values))
        except MySQLConnector.errors.IntegrityError as e:
            print(e)
            return False, str("Error: Name already taken")
        except e:
            print(e)
            return False, str("Unexpected database error")
        finally:
            connection.commit()
            cursor.close()
            connection.close()

        return True, str("No problemo in saving")

    def select_all(self, userid):
        """
        Select all rows
        :return: List of Dicts
        """
        
        try:
            connection = get_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(f"SELECT * FROM strategies where id = '{userid}'")
        except:
            return list()
        finally:
            rows = cursor.fetchall()
            connection.commit()
            #print(rows)
            cursor.close()
            connection.close()


        return rows

    def select_strategy(self, name, userid):
        """
        Select a certain strategy based on name
        :param name: String
        :return: Dict
        """

        try:
            connection = get_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute('''SELECT * FROM strategies WHERE name = %s and id = %s''', tuple([name,userid]))
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

def get_weights(name,id):

    try:
        connection = get_db()
        cursor = connection.cursor(dictionary=True)
        cursor.execute('''SELECT file FROM strategies WHERE name = %s and id = %s''', tuple([name,id]))
        row = cursor.fetchall()[0]
    finally:
        cursor.close()
        connection.close()

    return row