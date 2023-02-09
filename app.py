"""
FOCOS Flask app
"""
from flask import Flask, redirect, request, url_for, render_template, session, flash
from model.model import model
import time
from datetime import timedelta

app = Flask(__name__)
app.secret_key = b'y\x10\xbe\x01Pq\x1b7\x16f\xe2\xf9\x03\x12\x1aH'  # python -c 'import os; print(os.urandom(16))'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)  # clear session after five minutes of inactivity
model = model()
print("App started")


@app.route('/')
@app.route('/planning.html')
def planning():
    interventions = session.get("interventions")
    effects, principles = model.get_results(interventions)
    effects = [int(effect) for effect in effects]
    print("here you go", list(zip(principles, effects)))
    return render_template('planning.html', effects=effects, principles=principles)


@app.route('/slider', methods=['POST'])
def slider():
    form_input = request.form.to_dict(flat=True)
    intervention_sliders = {k: v for (k, v) in form_input.items() if
                            k in model.intervention_dict.keys()}  # Filter out non-slider input

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



# add route to strategies.html
@app.route('/strategies.html')
def strategies():
    interventions = session.get("strategy_interventions")
    entries = model.select_all()
    effects, principles = model.get_results(interventions)
    # change each element in effect from float to int
    effects = [int(effect) for effect in effects]
    description = session.get("description")
    name = session.get("name") if session.get("name") else "No Strategy Selected"
    strategy = {"name": name, "description": description, "effects": effects, "principles": principles}
    return render_template('strategies.html', entries=entries, strategy=strategy)


@app.route('/select_strategy', methods=['POST'])
def select_strategy():
    name = request.form.get("name")
    strategy = model.select_strategy(name)
    intervention_sliders = {k: v for (k, v) in strategy.items() if
                            k in model.intervention_dict.keys()}  # Filter out non-slider input
    session["strategy_interventions"] = intervention_sliders  # session["interventions"] is for the planning page
    session["name"] = name
    session["description"] = strategy["description"]
    return redirect(url_for('strategies'))


@app.route('/update_strategy', methods=['POST'])
def update_strategy():
    name = session.get("name")
    if not name:
        return redirect(url_for('strategies'))
    elif request.form.get("EditStrategy"):
        description = request.form.get("Description")
        new_name = request.form.get("new-Name")
        strategy = model.update_description(name, new_name, description)
        session["description"] = strategy["description"]
        session["name"] = strategy["name"]

    elif request.form.get("Delete"):
        model.delete_strategy(name)
        session["strategy_interventions"] = None
        session["description"] = None
        session["name"] = None
        session["strategies_to_compare"] = None

    return redirect(url_for('strategies'))


# add route to critic.html
# @app.route('/critic.html')
# def critic():
#     entries = model.select_all()
#
#     strategy_to_critique = session.get("strategy_to_critique")  # strategy selected for critique
#     practices = []
#     if strategy_to_critique:
#         strategy = model.select_strategy(strategy_to_critique)
#         strategy_practices_dict = {k: v for (k, v) in strategy.items() if
#                                    k in model.intervention_dict.keys() and v != 0}  # Filter out non-practice info and zero values
#         practices = [dict(key_name=k, full_name=model.intervention_dict[k]) for (k, v) in
#                      strategy_practices_dict.items()]  # Names
#
#     practice_to_critique = session.get("practice_to_critique")  # practice selected for critique
#     connections = {}
#     if practice_to_critique:
#         connections = model.get_practice_connections(practice_to_critique)
#
#     strategies_to_compare = None
#     effects, principles = model.get_results(None)  # get default values for effects
#     all_effects = [effects]
#
#     practice_sliders = session.get("practice_sliders")  # slider values for modified connections
#     new_practice_connections = {}
#     if practice_sliders and practice_to_critique:
#         new_practice_connections = dict(practice=model.intervention_dict[practice_to_critique],
#                                         connections=practice_sliders)
#         strategies_to_compare = ["Old", "New"]
#         effects, _ = model.get_results(strategy_practices_dict)  # get old values for effects
#         all_effects = [[int(effect) for effect in effects]]
#         effects, _ = model.get_results(strategy_practices_dict, new_practice_connections)  # get new values for effects
#         all_effects.append([int(effect) for effect in effects])
#
#     # Remove spaces and slashes from id_name (for html id) but not from name
#     connections = [dict(id_name=k.replace(" ", "").replace("/", ""), name=k, value=v) for (k, v) in connections.items()]
#
#     return render_template('critic.html', entries=entries, all_effects=all_effects,
#                            principles=principles, names=strategies_to_compare,
#                            practices=practices, connections=connections)
#
#
# @app.route('/critique_strategy', methods=['POST'])
# def critique_strategy():
#     strategy_to_critique = request.form.get("strategy_to_critique")
#     print(strategy_to_critique)
#     session["practice_to_critique"] = None
#     session["practice_sliders"] = None
#     session["strategy_to_critique"] = strategy_to_critique
#     return redirect(url_for('critic'))
#
#
# @app.route('/critique_practice', methods=['POST'])
# def critique_practice():
#     practice_to_critique = request.form.get("practice_to_critique")
#     print("this", practice_to_critique)
#     session["practice_to_critique"] = practice_to_critique
#     return redirect(url_for('critic'))
#
#
# @app.route('/critique_sliders', methods=['POST'])
# def critique_sliders():
#     form_input = request.form.to_dict(flat=True)
#     practice_sliders = {k: v for (k, v) in form_input.items() if
#                         k != "Submit"}  # Filter out non-practice input if there is any
#     session["practice_sliders"] = practice_sliders
#     return redirect(url_for('critic'))


# route to compare.html
@app.route('/compare.html')
def compare():
    entries = model.select_all()
    strategies_to_compare = session.get("strategies_to_compare")  # strategies selected for comparison
    effects, principles = model.get_results(None)  # get default values for effects

    all_effects = [effects]
    if strategies_to_compare:
        all_effects = []
        for name in strategies_to_compare:
            strategy = model.select_strategy(name)
            # Filter out non-slider input
            interventions = {k: v for (k, v) in strategy.items() if k in model.intervention_dict.keys()}
            print(interventions)
            effects, _ = model.get_results(interventions)
            effects = [int(effect) for effect in effects]
            all_effects.append(effects)
    return render_template('compare.html', entries=entries, all_effects=all_effects,
                           principles=principles, names=strategies_to_compare)


@app.route('/compare_strategies', methods=['POST'])
def compare_strategies():
    strategies_to_compare = []  # names
    for idx in range(5):
        strategy = request.form.get(f"strategies{idx}")
        if strategy:  # check if a strategy was selected
            if strategy not in strategies_to_compare:  # check for duplicate
                strategies_to_compare.append(strategy)

    print(strategies_to_compare)
    session["strategies_to_compare"] = strategies_to_compare
    return redirect(url_for('compare'))


@app.route('/compare_reset', methods=['POST'])
def compare_reset():
    session["strategies_to_compare"] = None
    return redirect(url_for('compare'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=False)
