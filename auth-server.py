from flask import Flask
from flask import request
from flask import jsonify

# noinspection PyUnresolvedReferences
from flask.ext.pymongo import PyMongo

application = Flask(__name__)
mongo = PyMongo(application)

CLIENT_SERVER_KEY = "d41d8cd98f00b204e9800998ecf8427e"

@application.route('/user/auth', methods=['POST'])
def user_auth():
    data = request.values
    client_id = data.get('client_id')
    encrypted_password = data.get('encrypted_password')
    return jsonify({})

class Authentication:
    def __init__(self):
        pass

if __name__ == '__main__':
    application.run()