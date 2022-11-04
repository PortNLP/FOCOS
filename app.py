"""
FOCOS Flask app
"""
from flask import Flask, redirect, request, url_for, render_template, session
from model.model import model
import time

app = Flask(__name__)
app.secret_key = b'y\x10\xbe\x01Pq\x1b7\x16f\xe2\xf9\x03\x12\x1aH' # python -c 'import os; print(os.urandom(16))'
model = model()
print("App started")

"""
Function decorator === app.route('/',planning())
"""


@app.route('/')

@app.route('/planning.html')
def planning():
    interventions = session.get("interventions")
    effects, principles = model.get_results(interventions)
    print(effects)
    return render_template('planning.html', effects=effects, principles=principles)

# route to the about page
@app.route('/about.html')
def about():
    return render_template('about.html')


@app.route('/slider', methods=['POST'])
def slider():
    form_input = request.form.to_dict(flat=True)
    intervention_sliders = {k:v for (k,v) in form_input.items() if k in model.intervention_dict.keys()} # Filter out non-slider input
    print(form_input)
    if request.form.get("Submit"): # This value isn't added to the form when submit is clicked
        session["interventions"] = intervention_sliders
    elif request.form.get("Save"):
        name = request.form.get("Name")
        comment = request.form.get("Comment")
        #model.save_strategy(intervention_sliders, name, comment)
    elif request.form.get("Reset"):
        session["interventions"] = {}
    return redirect(url_for('planning'))

@app.route('/strategies.html')
def strategies():
    interventions = session.get("interventions")
    entries = model.select_all()
    effects, principles = model.get_results(interventions)
    description = ""
    return render_template('strategies.html', entries=entries, description=description, effects=effects, principles=principles)

@app.route('/select_strategy', methods=['POST'])
def select_strategy():
    name = request.form.get("name")
    print(name)
    strategy = model.select_strategy(name)
    intervention_sliders = {k:v for (k,v) in strategy.items() if k in model.intervention_dict.keys()} # Filter out non-slider input
    session["interventions"] = intervention_sliders
    return redirect(url_for('strategies'))

if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=True, threaded=False)
