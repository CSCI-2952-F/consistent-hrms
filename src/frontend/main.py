import os

from flask import Flask, render_template

app = Flask('frontend', static_url_path='', static_folder='static', template_folder='templates')

HOSPITAL_NAME = os.environ.get('HOSPITAL_NAME', 'hospital_name')


@app.route('/', methods=['GET'])
def home():
    data = {
        'hospital_name': HOSPITAL_NAME,
    }
    return render_template('home.html', **data)

@app.route('/patient', methods=['GET'])
def patient():
    return render_template('patient.html')

@app.route('/physician', methods=['GET'])
def physician():
    return render_template('physician.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
