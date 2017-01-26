import base64
import datetime
import json
import random
import string

from Crypto.Cipher import AES
from flask import Flask
from flask import jsonify
from flask import request
from flask_pymongo import PyMongo

application = Flask(__name__)
mongo = PyMongo(application)

AUTH_SERVER_STORAGE_SERVER_KEY = "17771fab5708b94b42cfd00c444b6eaa"


@application.route('/client/create', methods=['GET'])
def client_create():
    db = mongo.db.dist
    db.clients.drop()
    db.clients.insert(
        {"client_id": "1"
            , "session_key": "F8C43DFA7C7E6E59C7358824AA11A"
            , "session_key_expires": (datetime.datetime.utcnow() + datetime.timedelta(seconds=60 * 60 * 4)).strftime(
            '%Y-%m-%d %H:%M:%S')
            , "public_key": "0123456789abcdef0123456789abcdef"
            , "password": "0dP1jO2zS7111111"}
    )
    return jsonify({})


@application.route('/client/auth', methods=['POST'])
def client_auth():
    db = mongo.db.dist
    data = request.get_json(force=True)
    client_id = data.get('client_id')
    encrypted_password = data.get('encrypted_password')
    current_client = db.clients.find_one({'client_id': client_id})
    pub_key = current_client['public_key']
    cypher = AES.new(pub_key, AES.MODE_ECB)
    decypher = cypher.decrypt(base64.b64decode(encrypted_password))
    pw = decypher.strip()
    if pw == current_client['password']:
        session_key = ''.join(
            random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(32))
        session_key_valid_time = (datetime.datetime.utcnow() + datetime.timedelta(seconds=60 * 250)).strftime(
            '%Y-%m-%d %H:%M:%S')
        current_client['session_key'] = session_key
        current_client['session_key_expires'] = session_key_valid_time
        if db.clients.update({'client_id': client_id}, current_client, upsert=True) != False:
            client = current_client
        else:
            return False
    else:
        return False
    if client:
        cypher2 = AES.new(AUTH_SERVER_STORAGE_SERVER_KEY, AES.MODE_ECB)
        val = client['session_key'] + b" " * (AES.block_size - len(client['session_key']) % AES.block_size)
        encoded_val = base64.b64encode(cypher2.encrypt(val))
        token = json.dumps({'session_key': client['session_key'],
                            'session_key_expires': client['session_key_expires'],
                            'server_host': "127.0.0.1",
                            'server_port': "8093",
                            'ticket': encoded_val})
        cypher3 = AES.new(client['public_key'], AES.MODE_ECB)
        val2 = token + b" " * (AES.block_size - len(token) % AES.block_size)
        encoded_val2 = base64.b64encode(cypher3.encrypt(val2))
        return jsonify({'success': True, 'token': encoded_val2})
    else:
        return jsonify({'success': False})


if __name__ == '__main__':
    application.run()
