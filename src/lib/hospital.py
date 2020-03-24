import os


def get_hospital_name():
    hospital_name = os.environ.get('HOSPITAL_NAME')
    if not hospital_name:
        raise Exception('Environment variable HOSPITAL_NAME not defined')
    return hospital_name
