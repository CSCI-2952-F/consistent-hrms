import os

BASE_PATH = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(os.path.join(BASE_PATH, 'pub.key')) as f:
    PUBLIC_KEY = f.read()

with open(os.path.join(BASE_PATH, 'priv.key')) as f:
    PRIVATE_KEY = f.read()
