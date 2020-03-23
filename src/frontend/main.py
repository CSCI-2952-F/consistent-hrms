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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
