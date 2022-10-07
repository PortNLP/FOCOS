"""
FOCOS Flask app
"""
from flask import Flask, redirect, request, url_for, render_template

from model_pylist import model

app = Flask(__name__)
model = model()

"""
Function decorator === app.route('/',index())
"""
@app.route('/')
@app.route('/index.html')
def index():

    principles=["PREOCCUPATION WITH FAILURE", "RELUCTANCE TO SIMPLIFY","COMMITMENT TO RESILIENCE",
      "DEFERENCE TO EXPERTISE","ORGANIZATIONAL RELIABILITY","SENSITIVITY TO OPERATION"]
    effects = model.get_results()
    entries = [dict(name=principle, value=effect) for principle, effect in zip (principles, effects)]
    return render_template('index.html', entries=entries)

@app.route('/data', methods=['POST'])
def submit():
    """
    Accepts POST requests, and processes the form;
    Redirect to index when completed.
    """
    model.input_intervention('Stop-Work-Authority', request.form['value'])
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
