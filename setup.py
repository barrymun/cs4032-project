import hashlib

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
    {"reference": hash_key.hexdigest(), "host": "localhost", "port": "9001", "master_server": True, "in_use": False})
hash_key.update("localhost" + ":" + "9002")
db.servers.insert(
    {"reference": hash_key.hexdigest(), "host": "localhost", "port": "9002", "master_server": False, "in_use": False})
