"""
FOCOS Flask app
"""
from flask import Flask, redirect, request, url_for, render_template, session, flash
from user.user import initUsers, User, get_user
from model.model import model, db
import time
import os
from werkzeug.utils import secure_filename
from util.util import allowed_file
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from Forms.webforms import LoginForm
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user

app = Flask(__name__)
f_type = "tanh"
app.secret_key = b'y\x10\xbe\x01Pq\x1b7\x16f\xe2\xf9\x03\x12\x1aH'  # python -c 'import os; print(os.urandom(16))'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)  # clear session after five minutes of inactivity
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@mysql/mydatabase'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = "/app/model"

db.init_app(app)
migrate = Migrate(app, db)
initUsers()
model = model()


print("App started")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
		
        user = User(username, password)

        if(user.is_authenticated()):
            login_user(user)
            session['userid'] = user.get_id()
            return redirect(url_for('planning'))
        else:
            flash("Wrong Password - Try Again!")

    return render_template('login.html', form=form)


@app.route('/planning.html')
@login_required
def planning():
    f_type = session.get('f_type', "tanh")
    interventions = session.get("interventions")
    file_name = session.get('FCM_FILE')
    effects, principles = model.get_results(interventions, function_type = f_type, file_name=file_name)
    effects = [int(effect) for effect in effects]
    # print("here you go", list(zip(principles, effects)))
    return render_template('planning.html', effects=effects, principles=principles, func_type=f_type, userid=session['userid'])


@app.route('/slider', methods=['POST'])
@login_required
def slider():
    form_input = request.form.to_dict(flat=True)
    intervention_sliders = {k: v for (k, v) in form_input.items() if
                            k in model.intervention_dict.keys()}  # Filter out non-slider input

    # print(form_input)
    if request.form.get("Submit"):
        session["interventions"] = intervention_sliders
    elif request.form.get("SaveStrategy"):
        name = request.form.get("Name")
        userid = current_user.get_id()
        description = request.form.get("Description")
        function_type = session.get('f_type', "tanh")
        if name:
            success = model.save_strategy(intervention_sliders, name, description, userid=userid, function_type=function_type)
            flash("Successfully saved strategy" if success else "Error: Name already taken")
        else:
            flash("Please enter a name")
    elif request.form.get("Reset"):
        session["interventions"] = {}
    return redirect(url_for('planning'))



# add route to strategies.html
@app.route('/strategies.html')
@login_required
def strategies():
    interventions = session.get("strategy_interventions")
    f_type = session.get('f_type', "tanh")
    userid = current_user.get_id()
    entries = model.select_all(userid)
    file_name = session.get('FCM_FILE')
    effects, principles = model.get_results(interventions, function_type = f_type, file_name = file_name)
    # change each element in effect from float to int
    effects = [int(effect) for effect in effects]
    description = session.get("description")
    name = session.get("name") if session.get("name") else "No Strategy Selected"
    strategy = {"name": name, "description": description, "effects": effects, "principles": principles, "function_type": session.get("f_type","tanh")}
    return render_template('strategies.html', entries=entries, strategy=strategy, func_type=f_type, userid=session['userid'])


@app.route('/select_strategy', methods=['POST'])
@login_required
def select_strategy():
    name = request.form.get("name")
    userid = current_user.get_id()
    strategy = model.select_strategy(name,userid)
    intervention_sliders = {k: v for (k, v) in strategy.items() if
                            k in model.intervention_dict.keys()}  # Filter out non-slider input
    session["strategy_interventions"] = intervention_sliders  # session["interventions"] is for the planning page
    session["name"] = name
    session["f_type"] = strategy['function_type']
    session["description"] = strategy["description"]
    return redirect(url_for('strategies'))


@app.route('/update_strategy', methods=['POST'])
@login_required
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
@login_required
def compare():
    f_type = session.get('f_type', "tanh")
    file_name = session.get('FCM_FILE')
    userid = current_user.get_id()
    entries = model.select_all(userid)
    strategies_to_compare = session.get("strategies_to_compare")  # strategies selected for comparison
    effects, principles = model.get_results(None)  # get default values for effects

    all_effects = [effects]
    if strategies_to_compare:
        all_effects = []
        for name in strategies_to_compare:
            userid = current_user.get_id()
            strategy = model.select_strategy(name,userid)
            # Filter out non-slider input
            strategy_ftype = strategy["function_type"]
            interventions = {k: v for (k, v) in strategy.items() if k in model.intervention_dict.keys()}
            # print(interventions)
            effects, _ = model.get_results(interventions, function_type = strategy_ftype)
            effects = [int(effect) for effect in effects]
            all_effects.append(effects)

    return render_template('compare.html', entries=entries, all_effects=all_effects,
                           principles=principles, names=strategies_to_compare, func_type=f_type, userid=session['userid'], file_name=file_name)


@app.route('/compare_strategies', methods=['POST'])
@login_required
def compare_strategies():
    strategies_to_compare = []  # names
    for idx in range(5):
        strategy = request.form.get(f"strategies{idx}")
        if strategy:  # check if a strategy was selected
            if strategy not in strategies_to_compare:  # check for duplicate
                strategies_to_compare.append(strategy)

    # print(strategies_to_compare)
    session["strategies_to_compare"] = strategies_to_compare
    return redirect(url_for('compare'))


@app.route('/compare_reset', methods=['POST'])
@login_required
def compare_reset():
    session["strategies_to_compare"] = None
    return redirect(url_for('compare'))

@app.route('/advanced.html', methods=['GET','POST'])
@login_required
def set_params():
    f_type = session.get('f_type',"tanh")
    weights = session.get('FCM_FILE','FCM-HROT_InterventionsIncluded.csv')

    if 'FCM_FILE' not in session:
        session['FCM_FILE'] = 'FCM-HROT_InterventionsIncluded.csv'

    return render_template('advanced.html',func_type=f_type, weights=weights)

@app.route('/UpdateSquashFunc', methods=['POST'])
@login_required
def UpdateSquashFunc():
    f_type = request.form.get('f_type')
    session['f_type'] = f_type if f_type != None else "tanh"

    if 'file' not in request.files:
            return redirect(url_for('set_params'))
    
    file = request.files['file']

    if file and allowed_file(file.filename):
        session['FCM_FILE'] = file.filename
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    elif file and not allowed_file(file.filename):
        flash('Only CSV file types are allowed')

    return redirect(url_for('set_params'))

@login_manager.user_loader
def load_user(user_id):
	return get_user(user_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=False)