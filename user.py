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

# response_body = request.text
# encoded_token = json.loads(response_body)["token"]
# cypher = AES.new(PUBLIC_KEY, AES.MODE_ECB)
# decypher = cypher.decrypt(base64.b64decode(encoded_token))
# decyphered_data = json.loads(decypher.strip())
# s_id = decyphered_data["s_id"]
# print("DECYPHER SUCCESS")
# print(s_id)
# access_key = decyphered_data["access_key"]
# server_host = decyphered_data["server_host"]
# server_port = decyphered_data["server_port"]
#
# cypher = AES.new(s_id, AES.MODE_ECB)
# encrypt_directory = "/home/test" + b" " * (AES.block_size - len("/home/test") % AES.block_size)
# directory = base64.b64encode(cypher.encrypt(encrypt_directory))
# encrypt_filename = "test.txt" + b" " * (AES.block_size - len("test.txt") % AES.block_size)
# filename = base64.b64encode(cypher.encrypt(encrypt_filename))
#
# data = open('test.txt', 'rb').read()
# headers = {'access_key': access_key, 'directory': directory, 'filename': filename}
# request = requests.post("http://" + server_host + ":" + server_port + "/f/upload", data=data, headers=headers)
# time.sleep(2)
# print request.text
# request2 = requests.post("http://" + server_host + ":" + server_port + "/f/delete", headers=headers)
# time.sleep(2)
# print request2.text

# request3 = requests.post("http://" + server_host + ":" + server_port + "/server/file/rollback", headers=headers)
# time.sleep(2)
# print request3.text
