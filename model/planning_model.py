from model.fcm import run_inference
import sqlite3
from datetime import date
DB_FILE = 'entries.db'    # file for our Database
FCM_MODEL = "V1"

class model():
    def __init__(self):

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
        self.current_strategy = {} # A strategy is a collection of interventions
        connection = sqlite3.connect(DB_FILE)
        cursor = connection.cursor()
        # Check if our database exists
        try: 
            cursor.execute("SELECT COUNT(rowid) FROM strategies")
        except sqlite3.OperationalError:
            definition = "CREATE TABLE strategies (model text, day text, name text, comment text"
            for intervention in self.intervention_names:
                definition += ", " + intervention + " real" # TODO: Integer should be fine
            definition = definition + ")"
            cursor.execute(definition)
        cursor.close()

    def input_interventions(self, intervention_sliders):
        """
        Input Interventions
        :param intervention_sliders: Dict {slider_name : value}
        :return: none
        """

        interventions = {}
        for key, val in intervention_sliders.items():
            name = self.intervention_dict[key]
            value = float(val) * 0.01   # Convert from percent; TODO: keep rounded to two decimal places
            interventions.update({name : value})
        self.current_strategy = interventions
        return True

    def get_results(self):
        """
        Gets the 5 degrees to which the HRO principles change
         in response to the latest strategy. Also returns the principle names
        :return: List of Floats, List of Strings
        """

        output_principle_names = []
        fcm_principle_names = []
        for key, val in self.principle_dict.items():
            output_principle_names.append(key)
            fcm_principle_names.append(val)

        if not self.current_strategy:  # no strategies
            effects = [0, 0, 0, 0, 0]
        else:
            # Get results for the latest strategy
            intervention = self.current_strategy
            #print(intervention)
            effects = run_inference(intervention, fcm_principle_names)

        return effects, output_principle_names

    def save_strategy(self, intervention_sliders, name, comment):
        """
        Save Current Strategy
        :param intervention_sliders: Dict {slider_name : value}
        :param name: String
        :param comment: String
        :return: none
        """
        
        intervention_values = [intervention_sliders[k] for k in self.intervention_names]
        day = date.today()
        model = FCM_MODEL
        connection = sqlite3.connect(DB_FILE)
        cursor = connection.cursor()
        cursor.execute("INSERT INTO strategies VALUES (?,?,?,?" +",?"*len(self.intervention_names)+")", (model, day, name, comment) + tuple(intervention_values))
        cursor.execute("SELECT * FROM strategies")
        print(cursor.fetchall())
        connection.commit()
        cursor.close()
        return True

    def select_all(self):
        connection = sqlite3.connect("test.db") # TODO: DB_FILE
        connection.row_factory = make_dicts
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM strategies")
        rows = cursor.fetchall()
        print(rows)
        cursor.close()
        
        return rows

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

# reset select edit delete