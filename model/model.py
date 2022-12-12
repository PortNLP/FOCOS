from model.fcm import run_inference, get_connections
import sqlite3
from datetime import date
DB_FILE = 'focos.db'    # file for our Database
FCM_MODEL = "V1"

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

        connection = sqlite3.connect(DB_FILE)
        cursor = connection.cursor()
        # Check if our database exists
        try: 
            cursor.execute("SELECT COUNT(rowid) FROM strategies")
        except sqlite3.OperationalError:
            definition = "CREATE TABLE strategies (model text, day text, name text NOT NULL PRIMARY KEY, description text"
            for intervention in self.intervention_names:
                definition += ", " + intervention + " INTEGER"
            definition = definition + ")"
            cursor.execute(definition)
        cursor.close()

    def get_results(self, intervention_sliders):
        """
        Gets the 5 degrees to which the HRO principles change
         in response to the latest strategy. Also returns the principle names
        :param intervention_sliders: Dict {slider_name : value}
        :return: List of Floats, List of Strings
        """

        output_principle_names = []
        fcm_principle_names = []
        for key, val in self.principle_dict.items(): #TODO: make these variables global
            output_principle_names.append(key)
            fcm_principle_names.append(val)


        if not intervention_sliders:  # no intervention
            effects = [0, 0, 0, 0, 0]
        else:
            interventions = {}
            for key, val in intervention_sliders.items():
                name = self.intervention_dict[key]
                value = float(val) * 0.01   # Convert from percent; TODO: keep rounded to two decimal places
                interventions.update({name : value})
            print(interventions)

            # Get results for the latest strategy
            effects = run_inference(interventions, fcm_principle_names)

        return effects, output_principle_names

    def get_practice_connections(self, practice_slider_name):
        """
        Get the connections for a certain practice      
        :param practice_slider_name: String
        :return: Dict {practice_name : value}
        """
        practice = self.intervention_dict[practice_slider_name]
        return get_connections(practice)

    def save_strategy(self, intervention_sliders, name, description):
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
        cursor = connection.cursor()
        sql = "INSERT INTO strategies VALUES (?,?,?,?" + ",?"*len(self.intervention_names) + ")"

        try:
            cursor.execute(sql, (model, day, name, description) + tuple(intervention_values))
        except sqlite3.IntegrityError as e:
            print(e)
            return False
        cursor.execute("SELECT * FROM strategies")
        print(cursor.fetchall())
        connection.commit()
        cursor.close()
        return True

    def select_all(self):
        """
        Select all rows
        :return: List of Dicts
        """
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM strategies")
        rows = cursor.fetchall()
        #print(rows)
        cursor.close()
        
        return rows

    def select_strategy(self, name):
        """
        Select a certain strategy based on name
        :param name: String
        :return: Dict
        """
        cursor = get_db().cursor()
        cursor.execute('''SELECT * FROM strategies WHERE name = ?''', (name,))
        row = cursor.fetchall()[0]
        print(row)
        cursor.close()
        
        return row

    def update_description(self, name, description):
        """
        Update a certain strategy based on name
        :param name: String
        :return: Dict
        """
        connection = get_db()
        cursor = connection.cursor()
        cursor.execute('''UPDATE strategies SET description = ? WHERE name = ?''', (description, name,))
        cursor.execute('''SELECT * FROM strategies WHERE name = ?''', (name,))
        row = cursor.fetchall()[0]
        print(row)
        connection.commit()
        cursor.close()
        
        return row

    def delete_strategy(self, name):
        """
        Delete a certain strategy based on name
        :param name: String
        :return: None
        """
        connection = get_db()
        cursor = connection.cursor()
        cursor.execute('''DELETE FROM strategies WHERE name = ?''', (name,))
        connection.commit()
        cursor.close()

        return True

def get_db():
    connection = None
    try:
        connection = sqlite3.connect(DB_FILE)
        connection.row_factory = make_dicts
    except Error as e:
        print(e)
    return connection

# results from the database are returned as dictionaries instead of tuples
def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

# reset select edit delete