"""
Data is stored in a Python list
"""
from datetime import date
from Model import Model

class model(Model):
    def __init__(self):
        self.interventions = []

    def get_results(self):
        """
        Gets the 5 degrees to which the HRO principles change
         in response to the latest intervention
        :return: List
        """
        
        if not self.interventions: # no interventions
            return [0,0,0,0,0]
        else:
            # Get results for self.interventions[-1]
            # return run_inference()
            return [1,2,3,4,5]

    def input_intervention(self, intervention, value):
        """
        Intervention
        :param intervention: String
        :param value: Integer
        :return: none
        """
        params = [intervention, value]
        self.interventions.append(params)
        return True
