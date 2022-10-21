"""
FOCOS Flask app
"""
from flask import Flask, redirect, request, url_for, render_template
from model.exploration_model import model

app = Flask(__name__)
model = model()

"""
Function decorator === app.route('/',exploration())
"""


@app.route('/')
@app.route('/exploration.html')
def exploration():

    effects, principles = model.get_results()
    return render_template('exploration.html', effects=effects, principles=principles)

@app.route('/slider', methods=['POST'])
def slider():
    form_input = request.form.to_dict(flat=True)
    print(form_input)
    intervention_sliders = {k:v for (k,v) in form_input.items() if k in model.intervention_dict.keys()} # Filter out non-slider input
    if request.form.get("Submit"):
        model.input_interventions(intervention_sliders)
    elif request.form.get("Save"):
        model.save_strategy(intervention_sliders)
    return redirect(url_for('exploration'))

if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=True)
