"""
FOCOS Flask app
"""
from datetime import datetime, timezone
import os
import shutil
import time
from files.files import delete_files_and_directories
from flask import Flask, redirect, request, url_for, render_template, session, flash, appcontext_tearing_down
from user.user import initUsers, User, get_user, update_last_active
from model.model import model, db
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
app.config["SESSION_PERMANENT"] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)  # clear session after five minutes of inactivity
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@mysql/mydatabase'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = "/app/temp"
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_THRESHOLD'] = 5

db.init_app(app)
migrate = Migrate(app, db)
initUsers()
model = model()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

user = None

print("App started")

@app.before_request
def before_request():

    now = datetime.now(timezone.utc)

    if 'userid' in session:
        userid = session['userid']
        
        if 'last_active' in session:
            last_active = session['last_active']
            delta = now - last_active
            five_seconds = timedelta(seconds=5)
            session['last_active'] = now

            # no need to stress the DB with constant updates when the user is active every 5 seconds or lesser
            if delta > five_seconds:
                update_last_active(userid, now)
        
        else:
            session['last_active'] = now


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

@app.route('/logout')
@login_required
def logout():

    logout_user()
    
    if session.get('userid'):
        # if session has expired we delete the user files with CRON job or other such tools
        directory_to_delete = os.path.join(app.config['UPLOAD_FOLDER'],session['userid'])
        delete_files_and_directories(directory_to_delete)
        del session['userid']

    if session.get('FCM_FILE'):
        del session['FCM_FILE']

    flash('You have successfully logged yourself out OR your session has expired.')
    return redirect('/login')

@app.route('/session-expired', methods=['POST'])
def session_expired_handler():
    return redirect(url_for('logout'))

@app.route('/planning.html')
@login_required
def planning():
    f_type = session.get('f_type', "tanh")
    interventions = session.get("interventions")
    file_name = session.get('FCM_FILE')

    if file_name is not None:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'],session['userid'],file_name)
    else:
        filepath = None

    effects, principles = model.get_results(interventions, function_type = f_type, file_name=filepath)
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
        file_name = session.get('FCM_FILE')

        if file_name:
            file_name = os.path.join("temp",session['userid'],session.get('FCM_FILE'))

        if name:
            success, msg = model.save_strategy(intervention_sliders, name, description, userid=userid, function_type=function_type,file_name=file_name)
            flash("Successfully saved strategy" if success else msg)
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
    name = session.get("name")
    file_name = session.get('FCM_FILE')

    if name is not None:
        effects, principles = model.get_strategy_results(name, userid, interventions, function_type = f_type)
    else:
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
    session['id'] = strategy['id']
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
            effects, _ = model.get_strategy_results(name, userid, interventions, function_type = strategy_ftype)
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
    weights = session.get('FCM_FILE')

    if not weights:
        weights = "FCM-HROT_InterventionsIncluded.csv"

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
        filename = secure_filename(file.filename)
        session['FCM_FILE'] = filename
        dirToMake = os.path.join(app.config['UPLOAD_FOLDER'],session['userid'])
        
        if os.path.exists(dirToMake):
        # If the directory exists, delete its contents
            for filename in os.listdir(dirToMake):
                file_path = os.path.join(dirToMake, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

        else:
            # If the directory doesn't exist, create it
            os.makedirs(dirToMake)
        

        file.save(os.path.join(dirToMake, session['FCM_FILE'] ))

    elif file and not allowed_file(file.filename):
        session['FCM_FILE'] = None
        flash('Only CSV file types are allowed')
    elif 'FCM_FILE' in session:
        session['FCM_FILE'] = None
        flash('FCM_FILE to be used is reset to default', category="info")

    return redirect(url_for('set_params'))

@login_manager.user_loader
def load_user(user_id):
	return get_user(user_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=False)