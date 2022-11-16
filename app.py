"""
FOCOS Flask app
"""
from flask import Flask, redirect, request, url_for, render_template, session, flash
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

@app.route('/slider', methods=['POST'])
def slider():
    form_input = request.form.to_dict(flat=True)
    intervention_sliders = {k:v for (k,v) in form_input.items() if k in model.intervention_dict.keys()} # Filter out non-slider input
    print(form_input)
    if request.form.get("Submit"):
        session["interventions"] = intervention_sliders
    elif request.form.get("SaveStrategy"):
        name = request.form.get("Name")
        description = request.form.get("Description")
        if name:
            success = model.save_strategy(intervention_sliders, name, description)
            flash("Successfully saved strategy" if success else "Error: Name already taken")
        else:
            flash("Please enter a name")
    elif request.form.get("Reset"):
        session["interventions"] = {}
    return redirect(url_for('planning'))


# route to the about page
@app.route('/about.html')
def about():
    return render_template('about.html')


@app.route('/strategies.html')
def strategies():
    interventions = session.get("strategy_interventions")
    entries = model.select_all()
    effects, principles = model.get_results(interventions)
    description = session.get("description")
    name = session.get("name") if session.get("name") else "No Strategy Selected"
    strategy = {"name" : name, "description" : description, "effects" : effects, "principles" : principles}
    return render_template('strategies.html', entries=entries, strategy=strategy)

@app.route('/select_strategy', methods=['POST'])
def select_strategy():
    name = request.form.get("name")
    print(name)
    strategy = model.select_strategy(name)
    intervention_sliders = {k:v for (k,v) in strategy.items() if k in model.intervention_dict.keys()} # Filter out non-slider input
    session["strategy_interventions"] = intervention_sliders # session["interventions"] is for the planning page
    session["name"] = name
    session["description"] = strategy["description"]
    return redirect(url_for('strategies'))

@app.route('/update_strategy', methods=['POST'])
def update_strategy():
    name = session.get("name")
    if request.form.get("EditStrategy"):
        description = request.form.get("Description")
        strategy = model.update_description(name, description)
        session["description"] = strategy["description"]
    elif request.form.get("Delete"):
        model.delete_strategy(name)

    return redirect(url_for('strategies'))


# route to compare.html
@app.route('/compare.html')
def compare():
    return render_template('compare.html')

if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=True, threaded=False)
