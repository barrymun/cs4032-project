import Queue
import base64
import datetime
import hashlib
import threading

from Crypto.Cipher import AES
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


def decrypt_data(key, hashed_val):
    decrypted_data = AES.new(key, AES.MODE_ECB).decrypt(base64.b64decode(hashed_val))
    return decrypted_data


@application.route('/file/download', methods=['POST'])
def download():
    print "\nDOWNLOADING ...\n"
    # data = request.get_json(force=True)
    headers = request.headers
    encrypted_filename = headers['filename']
    encrypted_directory = headers['directory']
    access_key = headers['access_key']

    session_id = decrypt_data(AUTH_KEY, access_key).strip()
    decrypted_directory = decrypt_data(session_id, encrypted_directory)
    decrypted_filename = decrypt_data(session_id, encrypted_filename)

    hash_key = hashlib.md5()
    hash_key.update(decrypted_directory)

    directory = db.directories.find_one(
        {"name": decrypted_directory, "reference": hash_key.hexdigest(), "server": server_instance()["reference"]})
    if not directory:
        return jsonify({"success": False})

    file = db.files.find_one(
        {"name": decrypted_filename, "directory": directory['reference'], "server": server_instance()["reference"]})
    if not file:
        return jsonify({"success": False})
    # return flask.send_file(file['reference'])
    return jsonify({"success": True})


@application.route('/file/upload', methods=['POST'])
def upload():
    print "\nUPLOADING ...\n"
    headers = request.headers
    encrypted_filename = headers['filename']
    encrypted_directory = headers['directory']
    access_key = headers['access_key']

    session_id = decrypt_data(AUTH_KEY, access_key).strip()
    decrypted_directory = decrypt_data(session_id, encrypted_directory)
    decrypted_filename = decrypt_data(session_id, encrypted_filename)

    hash_key = hashlib.md5()
    hash_key.update(decrypted_directory)

    if not db.directories.find_one(
            {"name": decrypted_directory, "reference": hash_key.hexdigest(), "server": server_instance()["reference"]}):
        hash_key = hashlib.md5()
        hash_key.update(decrypted_directory)
        db.directories.insert({"name": decrypted_directory
                                  , "reference": hash_key.hexdigest()
                                  , "server": server_instance()["reference"]})
        directory = db.directories.find_one(
            {"name": decrypted_directory, "reference": hash_key.hexdigest(), "server": server_instance()["reference"]})
    else:
        directory = db.directories.find_one(
            {"name": decrypted_directory, "reference": hash_key.hexdigest(), "server": server_instance()["reference"]})

    if not db.files.find_one(
            {"name": decrypted_filename, "directory": directory['reference'],
             "server": server_instance()["reference"]}):
        hash_key = hashlib.md5()
        hash_key.update(directory['reference'] + "/" + directory['name'])
        db.files.insert({"name": decrypted_filename
                            , "directory": directory['reference']
                            , "server": server_instance()["reference"]
                            , "reference": hash_key.hexdigest()
                            , "updated_at": datetime.datetime.utcnow()})
        file = db.files.find_one(
            {"name": decrypted_filename, "directory": directory['reference'], "server": server_instance()["reference"]})
    else:
        file = db.files.find_one(
            {"name": decrypted_filename, "directory": directory['reference'], "server": server_instance()["reference"]})

    if (server_instance()["master_server"]):
        thr = threading.Thread(target=upload_async, args=(file, headers), kwargs={})
        thr.start()
    return jsonify({'success': True})


@application.route('/file/delete', methods=['POST'])
def delete():
    print "\nDELETING ...\n"
    headers = request.headers
    encrypted_directory = headers['directory']
    encrypted_filename = headers['filename']
    access_key = headers['access_key']

    session_id = decrypt_data(AUTH_KEY, access_key).strip()
    decrypted_directory = decrypt_data(session_id, encrypted_directory)
    decrypted_filename = decrypt_data(session_id, encrypted_filename)

    hash_key = hashlib.md5()
    hash_key.update(decrypted_directory)

    if not db.directories.find_one(
            {"name": decrypted_directory, "reference": hash_key.hexdigest(), "server": server_instance()["reference"]}):
        print("No directory found")
        return jsonify({"success": False})
    else:
        directory = db.directories.find_one(
            {"name": decrypted_directory, "reference": hash_key.hexdigest(), "server": server_instance()["reference"]})
    file = db.files.find_one(
        {"name": decrypted_filename, "directory": directory['reference'], "server": server_instance()["reference"]})
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
