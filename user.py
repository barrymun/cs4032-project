import base64
import json
import time

import requests
from Crypto.Cipher import AES

PUBLIC_KEY = "0123456789abcdef0123456789abcdef"
client_id = "1"
decrypted_password = "0dP1jO2zS7111111"
request = requests.get("http://127.0.0.1:5000/client/auth")

#
# test connect to authentication server
#
cypher = AES.new(PUBLIC_KEY, AES.MODE_ECB)
encrypted_password = base64.b64encode(cypher.encrypt(decrypted_password))
headers = {'Content-type': 'application/json'}
payload = {'client_id': client_id, 'encrypted_password': encrypted_password}
request = requests.post("http://127.0.0.1:5000/client/auth", data=json.dumps(payload), headers=headers)
response_body = request.text
encoded_token = json.loads(response_body)["token"]
cypher = AES.new(PUBLIC_KEY, AES.MODE_ECB)
decypher = cypher.decrypt(base64.b64decode(encoded_token))
decyphered_data = json.loads(decypher.strip())
session_key = decyphered_data["session_key"]
print("DECYPHER SUCCESS")
print(session_key)
ticket = decyphered_data["ticket"]
server_host = decyphered_data["server_host"]
server_port = decyphered_data["server_port"]

#
# file uploads, file deletions, and transaction rollback tests
#
cypher = AES.new(session_key, AES.MODE_ECB)
encrypt_directory = "/home/test" + b" " * (AES.block_size - len("/home/test") % AES.block_size)
directory = base64.b64encode(cypher.encrypt(encrypt_directory))
encrypt_filename = "sample.txt" + b" " * (AES.block_size - len("sample.txt") % AES.block_size)
filename = base64.b64encode(cypher.encrypt(encrypt_filename))
data = open('test.txt', 'rb').read()
headers = {'ticket': ticket, 'directory': directory, 'filename': filename}
request = requests.post("http://" + server_host + ":" + server_port + "/server/file/upload", data=data, headers=headers)
time.sleep(2)
print request.text
request2 = requests.post("http://" + server_host + ":" + server_port + "/server/file/delete", headers=headers)
time.sleep(2)
print request2.text
# request3 = requests.post("http://" + server_host + ":" + server_port + "/server/file/rollback", headers=headers)
# time.sleep(2)
# print request3.text
