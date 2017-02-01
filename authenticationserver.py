import base64
import hashlib
import json
import random
import string

from Crypto.Cipher import AES
from flask import Flask
from flask import jsonify
from flask import request
from pymongo import MongoClient

mongo_server = "localhost"
mongo_port = "27017"
connect_string = "mongodb://" + mongo_server + ":" + mongo_port
connection = MongoClient(connect_string)
db = connection.project
db.users.drop()
db.servers.drop()
db.directories.drop()
db.files.drop()
db.transactions.drop()
hash_key = hashlib.md5()

hash_key.update("localhost" + ":" + "9001")
db.servers.insert(
    {"identifier": hash_key.hexdigest(), "host": "localhost", "port": "9001", "master_server": True, "in_use": False})

hash_key.update("localhost" + ":" + "9002")
db.servers.insert(
    {"identifier": hash_key.hexdigest(), "host": "localhost", "port": "9002", "master_server": False, "in_use": False})

hash_key.update("localhost" + ":" + "9002")
db.servers.insert(
    {"identifier": hash_key.hexdigest(), "host": "localhost", "port": "9003", "master_server": False, "in_use": False})

application = Flask(__name__)
mongo_server = "localhost"
mongo_port = "27017"
connect_string = "mongodb://" + mongo_server + ":" + mongo_port
connection = MongoClient(connect_string)
db = connection.project
AUTH_KEY = "17771fab5708b94b42cfd00c444b6eaa"


@application.route('/user/create', methods=['POST'])
def create_user():
    print "HERE"
    data = request.get_json(force=True)
    user_id = data.get('user_id')
    user_pwd = data.get('pwd')
    public_key = data.get('public_key')
    encrypt_user_pwd = base64.b64encode(AES.new(public_key, AES.MODE_ECB).encrypt(user_pwd))

    db.users.insert(
        {"user_id": user_id
            , "session_id": "F8C43DFA7C7E6E59C7358824AA11A"
            , "public_key": public_key
            , "pwd": encrypt_user_pwd}
    )
    return jsonify({})


@application.route('/user/auth', methods=['POST'])
def authorise_user():
    print "HERE 2"
    data = request.get_json(force=True)
    user_pwd = data.get('pwd')
    user_id = data.get('user_id')
    get_current_user = db.users.find_one({'user_id': user_id})
    encrypted_pwd = get_current_user['pwd']
    public_key = get_current_user['public_key']
    decrypt_user_pwd = AES.new(public_key, AES.MODE_ECB).decrypt(base64.b64decode(encrypted_pwd))
    pw = decrypt_user_pwd.strip()

    # print "\nuser_pwd = [ " + user_pwd + " ]\n"
    # print "\npw = [ " + pw + " ]\n"

    if pw == user_pwd:
        session_id = ''.join(
            random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(32))
        get_current_user['session_id'] = session_id
        if db.users.update({'user_id': user_id}, get_current_user, upsert=True) != False:
            user = get_current_user
        else:
            return None
    else:
        return None
    if user:
        hash_session_key = user['session_id'] + b" " * (AES.block_size - len(user['session_id']) % AES.block_size)
        encode_hash_session_key = base64.b64encode(AES.new(AUTH_KEY, AES.MODE_ECB).encrypt(hash_session_key))

        ticket = json.dumps({'session_id': user['session_id']
                                , 'server_host': "localhost"
                                , 'server_port': "9001"
                                , 'access_key': encode_hash_session_key})

        hash_ticket = ticket + b" " * (AES.block_size - len(ticket) % AES.block_size)
        encode_hash_ticket = base64.b64encode(AES.new(user['public_key'], AES.MODE_ECB).encrypt(hash_ticket))

        print "\nAUTHORISATION SUCCESSFUL\n"
        return jsonify({'success': True, 'ticket': encode_hash_ticket})
    else:
        return jsonify({'success': False})


if __name__ == '__main__':
    application.run()
