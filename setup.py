import hashlib

from pymongo import MongoClient

'''
Set up global variables here
'''
mongo_server = "127.0.0.1"
mongo_port = "27017"
connect_string = "mongodb://" + mongo_server + ":" + mongo_port

connection = MongoClient(connect_string)
db = connection.project  # equal to > use test_database
servers = db.servers

db.servers.drop()
db.directories.drop()
db.files.drop()

m = hashlib.md5()
m.update("127.0.0.1" + ":" + "8092")
db.servers.insert({"reference": m.hexdigest(), "host": "127.0.0.1", "port": "8092", "is_master": True, "in_use": False})
m.update("127.0.0.1" + ":" + "8093")
db.servers.insert(
    {"reference": m.hexdigest(), "host": "127.0.0.1", "port": "8093", "is_master": False, "in_use": False})
