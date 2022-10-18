"""
FOCOS Flask app
"""
from flask import Flask, redirect, request, url_for, render_template
from model.model_pylist import model

app = Flask(__name__)
model = model()

"""
Function decorator === app.route('/',exploration())
"""


@app.route('/')
@app.route('/exploration.html')
def exploration():
    principles = ["PREOCCUPATION WITH FAILURE", "RELUCTANCE TO SIMPLIFY", "COMMITMENT TO RESILIENCE",
                "DEFERENCE TO EXPERTISE",
                "SENSITIVITY TO OPERATION"]  # TODO: tie this to the principles variable in model_pylist.py

    effects = model.get_results()
    entries = [dict(name=principle, value=effect) for principle, effect in zip(principles, effects)]
    return render_template('exploration.html', entries=entries)


@app.route('/slider', methods=['POST'])
def slider():
    intervention_sliders = request.form.to_dict(flat=True)
    model.input_intervention(intervention_sliders)
    return redirect(url_for('exploration'))


if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=True)
