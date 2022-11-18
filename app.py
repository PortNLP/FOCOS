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
    print(list(zip(principles,effects)))
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
        session["strategy_interventions"] = None
        session["description"] = None
        session["name"] = None

    return redirect(url_for('strategies'))


# route to compare.html
@app.route('/compare.html')
def compare():
    entries = model.select_all()
    strategies_to_compare = session.get("strategies_to_compare")
    effects, principles = model.get_results(None) #  get default values for effects
    all_effects = [effects]
    if strategies_to_compare:
        all_effects = []
        for name in strategies_to_compare:
            strategy = model.select_strategy(name)
            # Filter out non-slider input
            interventions = {k:v for (k,v) in strategy.items() if k in model.intervention_dict.keys()} 
            print(interventions)
            effects, _ = model.get_results(interventions)
            all_effects.append(effects)
    #print(all_effects)
    #print(strategies_to_compare)
    return render_template('compare.html', entries=entries, all_effects=all_effects, 
                            principles=principles, names=strategies_to_compare)

@app.route('/compare_strategies', methods=['POST'])
def compare_strategies():
    #form_input = request.form.to_dict(flat=True)
    #print(form_input)
    strategies_to_compare = [] # names
    for idx in range(5):
        strategy = request.form.get(f"strategies{idx}")
        if strategy: # check if a strategy was selected
            if strategy not in strategies_to_compare: # check for duplicate
                strategies_to_compare.append(strategy)

    print(strategies_to_compare)
    session["strategies_to_compare"] = strategies_to_compare
    return redirect(url_for('compare'))

if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=True, threaded=False)
