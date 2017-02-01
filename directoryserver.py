import base64
import datetime
import hashlib
import threading

import flask
from Crypto.Cipher import AES
from diskcache import Cache
from flask import Flask
from flask import jsonify
from flask import request
from flask_pymongo import PyMongo
from pymongo import MongoClient

from transactions import ServerTransactions

application = Flask(__name__)
mongo = PyMongo(application)
mongo_server = "localhost"
mongo_port = "27017"
str = "mongodb://" + mongo_server + ":" + mongo_port
connection = MongoClient(str)
db = connection.project
servers = db.servers
server_transactions = ServerTransactions()
AUTH_KEY = "17771fab5708b94b42cfd00c444b6eaa"
SERVER_HOST = None
SERVER_PORT = None

# Set the cache location
cache = Cache('/tmp/mycachedir')


def asynchronous_upload(file, directory, headers):
    print "\nBEGINNING ASYNCHRONOUS UPLOAD ...\n"
    server_transactions.asynchronous_upload_transaction(file, directory, headers)


def asynchronous_delete(file, directory, headers):
    print "\nBEGINNING ASYNCHRONOUS DOWNLOAD ...\n"
    server_transactions.asynchronous_delete_transaction(file, directory, headers)


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
        {"name": decrypted_directory, "identifier": hash_key.hexdigest(), "server": server_instance()["identifier"]})
    if not directory:
        return jsonify({"success": False})

    file = db.files.find_one(
        {"name": decrypted_filename, "directory": directory['identifier'], "server": server_instance()["identifier"]})
    if not file:
        return jsonify({"success": False})

    cache_hash = file['identifier'] + "/" + directory['identifier'] + "/" + server_instance()["identifier"]
    if cache.get(cache_hash):
        return cache.get(cache_hash)
    else:
        return flask.send_file(file['identifier'])


@application.route('/file/upload', methods=['POST'])
def upload():
    print "\nUPLOADING ...\n"
    data = request.get_data()
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
            {"name": decrypted_directory, "identifier": hash_key.hexdigest(),
             "server": server_instance()["identifier"]}):
        hash_key = hashlib.md5()
        hash_key.update(decrypted_directory)
        db.directories.insert({"name": decrypted_directory
                                  , "identifier": hash_key.hexdigest()
                                  , "server": server_instance()["identifier"]})
        directory = db.directories.find_one(
            {"name": decrypted_directory, "identifier": hash_key.hexdigest(),
             "server": server_instance()["identifier"]})
    else:
        directory = db.directories.find_one(
            {"name": decrypted_directory, "identifier": hash_key.hexdigest(),
             "server": server_instance()["identifier"]})

    if not db.files.find_one(
            {"name": decrypted_filename, "directory": directory['identifier'],
             "server": server_instance()["identifier"]}):
        hash_key = hashlib.md5()
        hash_key.update(directory['identifier'] + "/" + directory['name'] + "/" + server_instance()['identifier'])
        db.files.insert({"name": decrypted_filename
                                   , "directory": directory['identifier']
                                   , "server": server_instance()["identifier"]
                                   , "identifier": hash_key.hexdigest()
                                   , "updated_at": datetime.datetime.utcnow()})

        file = db.files.find_one({'identifier': hash_key.hexdigest()})
        cache_hash = file['identifier'] + "/" + directory['identifier'] + "/" + server_instance()["identifier"]
        cache.set(cache_hash, data)
        with open(file['identifier'], "wb") as f:
            f.write(file['identifier'] + "/" + directory['identifier'] + "/" + server_instance()["identifier"])

        file = db.files.find_one(
            {"name": decrypted_filename, "directory": directory['identifier'],
             "server": server_instance()["identifier"]})
    else:
        file = db.files.find_one(
            {"name": decrypted_filename, "directory": directory['identifier'],
             "server": server_instance()["identifier"]})

    print "\nSERVER_HOST = [ " + SERVER_HOST + " ]\n"
    print "\nSERVER_PORT = [ " + SERVER_PORT + " ]\n"
    print server_instance()

    if (server_instance()["master_server"]):
        thr = threading.Thread(target=asynchronous_upload, args=(file['identifier'], directory['identifier'], headers),
                               kwargs={})
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
            {"name": decrypted_directory, "identifier": hash_key.hexdigest(),
             "server": server_instance()["identifier"]}):
        print("No directory found")
        return jsonify({"success": False})
    else:
        directory = db.directories.find_one(
            {"name": decrypted_directory, "identifier": hash_key.hexdigest(),
             "server": server_instance()["identifier"]})
    file = db.files.find_one(
        {"name": decrypted_filename, "directory": directory['identifier'], "server": server_instance()["identifier"]})
    if not file:
        print("No file found")
        return jsonify({"success": False})

    if (server_instance()["master_server"]):
        thr = threading.Thread(target=asynchronous_delete, args=(file['identifier'], directory['identifier'], headers),
                               kwargs={})
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
                db.servers.update({'identifier': current_server['identifier']}, current_server, upsert=True)
                application.run(host=current_server['host'], port=current_server['port'])
