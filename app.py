"""
FOCOS Flask app
"""
from flask import Flask, redirect, request, url_for, render_template
from model.planning_model import model

app = Flask(__name__)
model = model()

"""
Function decorator === app.route('/',planning())
"""


@app.route('/')

@app.route('/planning.html')
def planning():
    effects, principles = model.get_results()
    return render_template('planning.html', effects=effects, principles=principles)

# route to the about page
@app.route('/about.html')
def about():
    return render_template('about.html')


@app.route('/slider', methods=['POST'])
def slider():
    form_input = request.form.to_dict(flat=True)
    print(form_input)
    intervention_sliders = {k:v for (k,v) in form_input.items() if k in model.intervention_dict.keys()} # Filter out non-slider input
    if request.form.get("Submit"):
        model.input_interventions(intervention_sliders)
    elif request.form.get("Save"):
        name = request.form.get("Name")
        comment = request.form.get("Comment")
        model.save_strategy(intervention_sliders, name, comment)
    return redirect(url_for('planning'))

if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=True)
