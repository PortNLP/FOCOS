"""
Data is stored in a Python list
"""
from datetime import date
from model.Model import Model
from model.fcm import run_inference


class model(Model):
  def __init__(self):
    self.interventions = []

  def get_results(self):
    """
        Gets the 5 degrees to which the HRO principles change
         in response to the latest intervention
        :return: List
        """

    principles = ["PREOCCUPATION WITH FAILURE", "RELUCTANCE TO SIMPLIFY", "COMMITMENT TO RESILIENCE",
                  "DEFERENCE TO EXPERTISE", "SENSITIVITY TO OPERATION"]

    if not self.interventions:  # no interventions
      return [0, 0, 0, 0, 0]
    else:
      # Get results for the latest intervention
      intervention = [self.interventions[-1]]
      print(intervention)
      return run_inference(intervention, principles)

  def input_intervention(self, name, value):
    """
        Intervention
        :param name: String
        :param value: Integer
        :return: none
        """

    value = float(value) * 0.01  # Convert from percent
    intervention = dict(name=name, value=value)
    self.interventions.append(intervention)
    return True
