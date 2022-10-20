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

    effects, principles = model.get_results()
    return render_template('exploration.html', effects=effects, principles=principles)


@app.route('/slider', methods=['POST'])
def slider():
    intervention_sliders = request.form.to_dict(flat=True)
    model.input_intervention(intervention_sliders)
    return redirect(url_for('exploration'))


if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=True)
