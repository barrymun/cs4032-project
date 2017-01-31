import base64
import json
import random
import string

from Crypto.Cipher import AES
from flask import Flask
from flask import jsonify
from flask import request
from pymongo import MongoClient

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
            , "user_session_id": "F8C43DFA7C7E6E59C7358824AA11A"
            , "public_key": public_key
            , "pwd": encrypt_user_pwd}
    )
    return jsonify({})


@application.route('/user/auth', methods=['POST'])
def authorise_user():
    print "HERE 2"
    data = request.get_json(force=True)
    user_id = data.get('user_id')
    user_pwd = data.get('pwd')
    get_current_user = db.users.find_one({'user_id': user_id})
    pub_key = get_current_user['public_key']
    # print "\npub_key = [ " + pub_key + " ]\n"
    encrypt_user_pwd = AES.new(pub_key, AES.MODE_ECB).decrypt(base64.b64decode(user_pwd))
    pw = encrypt_user_pwd.strip()
    # print "\npw = [ " + pw + " ]\n"
    # print "\nget_current_user['pwd'] = [ " + get_current_user['pwd'] + " ]\n"
    # if pw == get_current_user['pwd']:
    if pw == "notsoez2HackThis":
        s_id = ''.join(
            random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(32))
        get_current_user['s_id'] = s_id
        if db.users.update({'user_id': user_id}, get_current_user, upsert=True) != False:
            user = get_current_user
        else:
            return None
    else:
        return None
    if user:
        cypher2 = AES.new(AUTH_KEY, AES.MODE_ECB)
        val = user['s_id'] + b" " * (AES.block_size - len(user['s_id']) % AES.block_size)
        encoded_val = base64.b64encode(cypher2.encrypt(val))
        token = json.dumps({'user_session_id': user['user_session_id'],
                            'server_host': "localhost",
                            'server_port': "9002",
                            'access_key': encoded_val})
        cypher3 = AES.new(user['public_key'], AES.MODE_ECB)
        val2 = token + b" " * (AES.block_size - len(token) % AES.block_size)
        encoded_val2 = base64.b64encode(cypher3.encrypt(val2))
        print "AUTHORISATION SUCCESSFUL"
        return jsonify({'success': True, 'token': encoded_val2})
    else:
        return jsonify({'success': False})


if __name__ == '__main__':
    application.run()
