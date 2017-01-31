import base64
import json

import requests
from Crypto.Cipher import AES
from pymongo import MongoClient

# mongo setup stuff
mongo_server = "localhost"
mongo_port = "27017"
connect_string = "mongodb://" + mongo_server + ":" + mongo_port
connection = MongoClient(connect_string)
db = connection.project

# user info - this file is essentially the first user
user_id = "1"
PUBLIC_KEY = "4ThisIsARandomlyGenAESpublicKey4"
user_pwd = "notsoez2HackThis"

# required encyption pre-requiste variables
secret_hash = AES.new(PUBLIC_KEY, AES.MODE_ECB)

headers = {'Content-type': 'application/json'}
payload = {'user_id': user_id
    , 'pwd': user_pwd
    , 'public_key': PUBLIC_KEY}
request = requests.post("http://localhost:5000/user/create", data=json.dumps(payload), headers=headers)

headers = {'Content-type': 'application/json'}
payload = {'user_id': user_id
    , 'pwd': user_pwd}
request = requests.post("http://localhost:5000/user/auth", data=json.dumps(payload), headers=headers)

if (request != None):
    print "CONTINUE WITH NEXT STEPS HERE - FILE MANAGEMENT"

    server_response = request.text
    encoded_hashed_ticket = json.loads(server_response)["ticket"]
    decoded_hashed_ticked = secret_hash.decrypt(base64.b64decode(encoded_hashed_ticket))
    data = json.loads(decoded_hashed_ticked.strip())

    session_id = data["session_id"]
    server_host = data["server_host"]
    server_port = data["server_port"]
    access_key = data["access_key"]
    virtual_structure_hash = AES.new(session_id, AES.MODE_ECB)

    print ""
    print data
    print ""

    print("DATA DECRYPTION SUCCESS")

    directory = "/fileserver/location"
    filename = "test-files/test.txt"
    encrpyted_directory = base64.b64encode(
        virtual_structure_hash.encrypt(directory + b" " * (AES.block_size - len(directory) % AES.block_size)))
    encrpyted_filename = base64.b64encode(
        virtual_structure_hash.encrypt(filename + b" " * (AES.block_size - len(filename) % AES.block_size)))

    data = open('test-files/test.txt', 'rb').read()
    headers = {'access_key': access_key
        , 'directory': encrpyted_directory
        , 'filename': encrpyted_filename}

    request = requests.post("http://" + server_host + ":" + server_port + "/file/upload", data=data, headers=headers)
    print request.text

    request = requests.post("http://" + server_host + ":" + server_port + "/file/download", headers=headers)
    print request.text

    request2 = requests.post("http://" + server_host + ":" + server_port + "/file/delete", headers=headers)
    print request2.text
