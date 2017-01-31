import base64
import json

import requests
from Crypto.Cipher import AES
from pymongo import MongoClient

mongo_server = "localhost"
mongo_port = "27017"
connect_string = "mongodb://" + mongo_server + ":" + mongo_port
connection = MongoClient(connect_string)
db = connection.project

PUBLIC_KEY = "4ThisIsARandomlyGenAESpublicKey4"
user_id = "1"
user_pwd = "notsoez2HackThis"

cypher = AES.new(PUBLIC_KEY, AES.MODE_ECB)
encrypt_user_pwd = base64.b64encode(cypher.encrypt(user_pwd))

headers = {'Content-type': 'application/json'}
payload = {'user_id': user_id,
           'pwd': user_pwd,
           'public_key': PUBLIC_KEY}
request = requests.post("http://localhost:5000/user/create", data=json.dumps(payload), headers=headers)

headers = {'Content-type': 'application/json'}
payload = {'user_id': user_id,
           'pwd': encrypt_user_pwd,
           'public_key': PUBLIC_KEY}
request = requests.post("http://localhost:5000/user/auth", data=json.dumps(payload), headers=headers)

if (request != None):
    print "CONTINUE WITH NEXT STEPS HERE - FILE MANAGEMENT"

    server_response = request.text
    print "\nserver_response = [ " + server_response + " ]"
    encoded_token = json.loads(server_response)["token"]
    print "\nencoded_token = [ " + encoded_token + " ]"
    cypher = AES.new(PUBLIC_KEY, AES.MODE_ECB)
    decypher = cypher.decrypt(base64.b64decode(encoded_token))
    data = json.loads(decypher.strip())
    user_session_id = data["user_session_id"]
    # print(user_session_id)
    access_key = data["access_key"]
    server_host = data["server_host"]
    server_port = data["server_port"]
    print("DATA DECRYPTION SUCCESS")

    directory = "/fileserver/location"
    filename = "test-files/test.txt"

    data = open('test-files/test.txt', 'rb').read()
    headers = {'access_key': access_key, 'directory': directory, 'filename': filename}

    request = requests.post("http://" + server_host + ":" + server_port + "/file/upload", data=data, headers=headers)
    # time.sleep(2)
    print request.text

    request = requests.post("http://" + server_host + ":" + server_port + "/file/download", headers=headers)
    # time.sleep(2)
    print request.text

    request2 = requests.post("http://" + server_host + ":" + server_port + "/file/delete", headers=headers)
    # time.sleep(2)
    print request2.text

    # request3 = requests.post("http://" + server_host + ":" + server_port + "/server/file/rollback", headers=headers)
    # time.sleep(2)
    # print request3.text
