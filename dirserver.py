import Queue
import datetime
import hashlib
import threading

from flask import Flask
from flask import jsonify
from flask import request
from flask_pymongo import PyMongo
from pymongo import MongoClient

from transactions import ServerTransactions

application = Flask(__name__)
mongo = PyMongo(application)
write_lock = threading.Lock()
write_queue = Queue.Queue(maxsize=100)
mongo_server = "localhost"
mongo_port = "27017"
connect_string = "mongodb://" + mongo_server + ":" + mongo_port
connection = MongoClient(connect_string)
db = connection.project
servers = db.servers
server_transactions = ServerTransactions()
AUTH_KEY = "17771fab5708b94b42cfd00c444b6eaa"
SERVER_HOST = None
SERVER_PORT = None


def upload_async(file, client_request):
    server_transactions.upload_async_trans(file, client_request)


def delete_async(client_request):
    server_transactions.delete_async_transaction(client_request)


def server_instance():
    with application.app_context():
        return db.servers.find_one({"host": SERVER_HOST, "port": SERVER_PORT})


@application.route('/file/download', methods=['POST'])
def download():
    print "\nDOWNLOADING ...\n"
    # data = request.get_json(force=True)
    headers = request.headers
    filename = headers['filename']
    dir_ref = headers['directory']
    hash_key = hashlib.md5()
    hash_key.update(dir_ref)
    directory = db.directories.find_one(
        {"name": dir_ref, "reference": hash_key.hexdigest(), "server": server_instance()["reference"]})
    if not directory:
        return jsonify({"success": False})

    file = db.files.find_one(
        {"name": filename, "directory": directory['reference'], "server": server_instance()["reference"]})
    if not file:
        return jsonify({"success": False})
    # return flask.send_file(file['reference'])
    return jsonify({"success": True})


@application.route('/file/upload', methods=['POST'])
def upload():
    print "\nUPLOADING ...\n"
    headers = request.headers
    file_name_hash = headers['filename']
    directory_name_hash = headers['directory']
    access_key = headers['access_key']
    hash_key = hashlib.md5()
    hash_key.update(directory_name_hash)

    if not db.directories.find_one(
            {"name": directory_name_hash, "reference": hash_key.hexdigest(), "server": server_instance()["reference"]}):
        hash_key = hashlib.md5()
        hash_key.update(directory_name_hash)
        db.directories.insert({"name": directory_name_hash
                                  , "reference": hash_key.hexdigest()
                                  , "server": server_instance()["reference"]})
        directory = db.directories.find_one(
            {"name": directory_name_hash, "reference": hash_key.hexdigest(), "server": server_instance()["reference"]})
    else:
        directory = db.directories.find_one(
            {"name": directory_name_hash, "reference": hash_key.hexdigest(), "server": server_instance()["reference"]})

    if not db.files.find_one(
            {"name": file_name_hash, "directory": directory['reference'], "server": server_instance()["reference"]}):
        hash_key = hashlib.md5()
        hash_key.update(directory['reference'] + "/" + directory['name'])
        db.files.insert({"name": file_name_hash
                            , "directory": directory['reference']
                            , "server": server_instance()["reference"]
                            , "reference": hash_key.hexdigest()
                            , "updated_at": datetime.datetime.utcnow()})
        file = db.files.find_one(
            {"name": file_name_hash, "directory": directory['reference'], "server": server_instance()["reference"]})
    else:
        file = db.files.find_one(
            {"name": file_name_hash, "directory": directory['reference'], "server": server_instance()["reference"]})

    if (server_instance()["master_server"]):
        thr = threading.Thread(target=upload_async, args=(file, headers), kwargs={})
        thr.start()
    return jsonify({'success': True})


@application.route('/file/delete', methods=['POST'])
def delete():
    print "\nDELETING ...\n"
    headers = request.headers
    directory_name_hash = headers['directory']
    file_name_hash = headers['filename']
    access_key = headers['access_key']
    # s_id = decode(AUTH_KEY, access_key).strip()
    # dir_ref = decode(s_id, directory_name_hash)
    # filename = decode(s_id, file_name_hash)
    hash_key = hashlib.md5()
    hash_key.update(directory_name_hash)

    if not db.directories.find_one(
            {"name": directory_name_hash, "reference": hash_key.hexdigest(), "server": server_instance()["reference"]}):
        print("No directory found")
        return jsonify({"success": False})
    else:
        directory = db.directories.find_one(
            {"name": directory_name_hash, "reference": hash_key.hexdigest(), "server": server_instance()["reference"]})
    file = db.files.find_one(
        {"name": file_name_hash, "directory": directory['reference'], "server": server_instance()["reference"]})
    if not file:
        print("No file found")
        return jsonify({"success": False})

    if (server_instance()["master_server"]):
        thr = threading.Thread(target=delete_async, args=(file, headers), kwargs={})
        thr.start()
    return jsonify({'success': True})


if __name__ == '__main__':
    with application.app_context():
        for current_server in db.servers.find():
            print(current_server)
            if (current_server['in_use'] == False):
                current_server['in_use'] = True
                SERVER_PORT = current_server['port']
                SERVER_HOST = current_server['host']
                db.servers.update({'reference': current_server['reference']}, current_server, upsert=True)
                application.run(host=current_server['host'], port=current_server['port'])
