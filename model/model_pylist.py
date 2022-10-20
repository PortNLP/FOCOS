"""
Data is stored in a Python list
"""
from datetime import date
from model.Model import Model
from model.fcm import run_inference


class model(Model):
    def __init__(self):
        self.strategies = []  # A strategy is a collection of interventions

    def get_results(self):
        """
        Gets the 5 degrees to which the HRO principles change
         in response to the latest strategy. Also returns the principle names
        :return: List of Floats, List of Strings
        """

        #principles = ["PREOCCUPATION WITH FAILURE", "RELUCTANCE TO SIMPLIFY", "COMMITMENT TO RESILIENCE", "DEFERENCE TO EXPERTISE", "SENSITIVITY TO OPERATION"]

        # Dict {fcm_principle_name : output_principle_name}
        principle_dict = {
            "Deference to Expertise" :      "DEFERENCE TO EXPERTISE",  
            "Commitment to Resilience" :    "COMMITMENT TO RESILIENCE",
            "Sensitivity to Operations" :   "SENSITIVITY TO OPERATION",
            "Reluctance to Simplify " :     "RELUCTANCE TO SIMPLIFY",  
            "Preoccupation With Failure" :  "PREOCCUPATION WITH FAILURE"
        }

        output_principle_names = []
        fcm_principle_names = []
        for key, val in principle_dict.items():
            output_principle_names.append(key)
            fcm_principle_names.append(val)


        if not self.strategies:  # no strategies
            effects = [0, 0, 0, 0, 0]
        else:
            # Get results for the latest strategy
            intervention = self.strategies[-1]
            print(intervention)
            effects = run_inference(intervention, fcm_principle_names)

        return effects, output_principle_names

    def input_intervention(self, intervention_sliders):
        """
        Input Interventions
        :param intervention_sliders: Dict {slider_name : value}
        :return: none
        """

        # Dict {slider_name : intervention_name}
        intervention_dict = {
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

        interventions = {}
        for key, val in intervention_sliders.items():
            value = float(val) * 0.01   # Convert from percent; TODO: keep rToounded to two decimal places
            name = intervention_dict[key]
            interventions.update({name : value})
        self.strategies.append(interventions)
        return True
