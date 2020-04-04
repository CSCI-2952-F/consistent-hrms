import os

from flask import Flask, render_template

app = Flask('frontend', static_url_path='', static_folder='static', template_folder='templates')

HOSPITAL_NAME = os.environ.get('HOSPITAL_NAME', 'hospital_name')
API_GATEWAY_PORT = os.environ.get('API_GATEWAY_PORT', 'api_gateway_port')


@app.route('/', methods=['GET'])
def home():
    data = {
        'hospital_name': HOSPITAL_NAME,
    }
    return render_template('home.html', **data)

@app.route('/patient', methods=['GET'])
def patient():
    data = {
        'hospital_name': HOSPITAL_NAME,
        'api_gateway_port': API_GATEWAY_PORT
    }
    return render_template('patient.html', **data)

@app.route('/physician', methods=['GET'])
def physician():
    data = {
        'hospital_name': HOSPITAL_NAME,
        'api_gateway_port': API_GATEWAY_PORT
    }    
    return render_template('physician.html', **data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
