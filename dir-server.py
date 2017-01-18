import base64
import md5
import datetime
import json
import hashlib
import flask
import os
import threading
import requests
import redis
import zlib
import uuid
import Queue

from flask import Flask
from flask import request
from flask import jsonify
from flask import Response
from flask_pymongo import PyMongo
from pymongo import MongoClient
from Crypto.Cipher import AES

application = Flask(__name__)
mongo = PyMongo(application)
write_lock = threading.Lock()
write_queue = Queue.Queue(maxsize=100)
'''
Set up global variables here
'''

mongo_server = "127.0.0.1"
mongo_port = "27017"
connect_string = "mongodb://" + mongo_server + ":" + mongo_port

connection = MongoClient(connect_string)
db = connection.project  # equal to > use test_database
servers = db.servers

# constants
AUTH_SERVER_STORAGE_SERVER_KEY = "d41d8cd98f00b204e9800998ecf8427e"
SERVER_HOST = None
SERVER_PORT = None


def reset():
    db.directories.drop()
    db.files.drop()


def upload_async(file, client_request):
    with application.app_context():
        servers = db.servers.find()
        for server in servers:
            host = server["host"]
            port = server["port"]
            if (host == SERVER_HOST and port == SERVER_PORT):
                continue
            # make POST request to upload file to server, using
            # same client request
            data = open(file['reference'], 'rb').read()
            print(client_request)

            headers = {'ticket': client_request['ticket'],
                       'directory': client_request['directory'],
                       'filename': client_request['filename']}
            r = requests.post("http://" + host + ":" + port + "/server/file/upload", data=data, headers=headers)


def delete_async(client_request):
    with application.app_context():
        servers = db.servers.find()
        for server in servers:
            host = server["host"]
            port = server["port"]
            if (host == SERVER_HOST and port == SERVER_PORT):
                continue
            # make POST request to delete file from server, using
            # same client request
            print(client_request)

            headers = {'ticket': client_request['ticket'],
                       'directory': client_request['directory'],
                       'filename': client_request['filename']}
            r = requests.post("http://" + host + ":" + port + "/server/file/delete", data='', headers=headers)


def rollback_async(client_request):
    with application.app_context():
        servers = db.servers.find()
        for server in servers:
            host = server["host"]
            port = server["port"]
            if (host == SERVER_HOST and port == SERVER_PORT):
                continue
            # make POST request to delete file from server, using
            # same client request
            print(client_request)

            headers = {'ticket': client_request['ticket'],
                       'directory': client_request['directory'],
                       'filename': client_request['filename']}
            r = requests.post("http://" + host + ":" + port + "/server/file/rollback", data='', headers=headers)


def get_current_server():
    with application.app_context():
        return db.servers.find_one({"host": SERVER_HOST, "port": SERVER_PORT})


def get_total_servers():
    with application.app_context():
        return count(db.servers.find({}))


@application.route('/server/file/upload', methods=['POST'])
def file_upload():
    # Need to update cached record (if exists)
    pre_write_cache_reference = uuid.uuid4()
    print(Cache.compress(request.get_data()))
    cache.create(pre_write_cache_reference, Cache.compress(request.get_data()))
    print cache.get(pre_write_cache_reference)

    headers = request.headers

    filename_encoded = headers['filename']
    directory_name_encoded = headers['directory']
    ticket = headers['ticket']
    session_key = Authentication.decode(AUTH_SERVER_STORAGE_SERVER_KEY, ticket).strip()
    directory_name = Authentication.decode(session_key, directory_name_encoded)
    filename = Authentication.decode(session_key, filename_encoded)

    m = hashlib.md5()
    m.update(directory_name)
    server = get_current_server()

    if not db.directories.find_one(
            {"name": directory_name, "reference": m.hexdigest(), "server": get_current_server()["reference"]}):
        directory = Directory.create(directory_name, server["reference"])
    else:
        directory = db.directories.find_one(
            {"name": directory_name, "reference": m.hexdigest(), "server": get_current_server()["reference"]})

    if not db.files.find_one(
            {"name": filename, "directory": directory['reference'], "server": get_current_server()["reference"]}):
        file = File.create(filename, directory['name'], directory['reference'], get_current_server()["reference"])
    else:
        file = db.files.find_one(
            {"name": filename, "directory": directory['reference'], "server": get_current_server()["reference"]})

    transaction = Transaction(write_lock, file['reference'], directory['reference'], pre_write_cache_reference)
    transaction.start()

    if (get_current_server()["is_master"]):
        thr = threading.Thread(target=upload_async, args=(file, headers), kwargs={})
        thr.start()  # will run "foo"
    return jsonify({'success': True})


@application.route('/server/file/download', methods=['POST'])
def file_download():
    data = request.get_json(force=True)
    authentication = data.get('authentication')

    filename = data.get('filename')
    directory_name = data.get('directory')

    m = hashlib.md5()
    m.update(directory_name)
    directory = db.directories.find_one(
        {"name": directory_name, "reference": m.hexdigest(), "server": get_current_server()["reference"]})
    if not directory:
        return jsonify({"success": False})

    file = db.files.find_one(
        {"name": filename, "directory": directory['reference'], "server": get_current_server()["reference"]})
    if not file:
        return jsonify({"success": False})

    cache_file_reference = directory['reference'] + "_" + file['reference']
    if cache.exists(cache_file_reference):
        return Cache.decompress(cache.get(cache_file_reference))
    else:
        return flask.send_file(file["reference"])


@application.route('/server/file/rollback', methods=['POST'])
def file_rollback():
    headers = request.headers
    filename_encoded = headers['filename']
    directory_name_encoded = headers['directory']
    ticket = headers['ticket']
    session_key = Authentication.decode(AUTH_SERVER_STORAGE_SERVER_KEY, ticket).strip()
    directory_name = Authentication.decode(session_key, directory_name_encoded)
    filename = Authentication.decode(session_key, filename_encoded)

    m = hashlib.md5()
    m.update(directory_name)
    server = get_current_server()
    print(server)
    # check if the directory exists on current server
    if not db.directories.find_one(
            {"name": directory_name, "reference": m.hexdigest(), "server": get_current_server()["reference"]}):
        print("No directory found")
        return jsonify({"success": False})
    else:
        directory = db.directories.find_one(
            {"name": directory_name, "reference": m.hexdigest(), "server": get_current_server()["reference"]})
    # check if the file exists on current server
    file = db.files.find_one(
        {"name": filename, "directory": directory['reference'], "server": get_current_server()["reference"]})
    if not file:
        print("No file found")
        return jsonify({"success": False})

    rollback_transaction = RollbackTransaction(write_lock, file["reference"], directory["reference"])
    rollback_transaction.start()

    if (get_current_server()["is_master"]):
        thr = threading.Thread(target=rollback_async, args=(file, headers), kwargs={})
        thr.start()  # will run "foo"
    return jsonify({'success': True})




@application.route('/server/file/delete', methods=['POST'])
def file_delete():
    headers = request.headers
    filename_encoded = headers['filename']
    directory_name_encoded = headers['directory']
    ticket = headers['ticket']
    session_key = Authentication.decode(AUTH_SERVER_STORAGE_SERVER_KEY, ticket).strip()
    directory_name = Authentication.decode(session_key, directory_name_encoded)
    filename = Authentication.decode(session_key, filename_encoded)

    m = hashlib.md5()
    m.update(directory_name)
    server = get_current_server()
    print(server)
    # check if the directory exists on current server
    if not db.directories.find_one(
            {"name": directory_name, "reference": m.hexdigest(), "server": get_current_server()["reference"]}):
        print("No directory found")
        return jsonify({"success": False})
    else:
        directory = db.directories.find_one(
            {"name": directory_name, "reference": m.hexdigest(), "server": get_current_server()["reference"]})
    # check if the file exists on current server
    file = db.files.find_one(
        {"name": filename, "directory": directory['reference'], "server": get_current_server()["reference"]})
    if not file:
        print("No file found")
        return jsonify({"success": False})

    delete_transaction = DeleteTransaction(write_lock, file["reference"], directory["reference"])
    delete_transaction.start()

    if (get_current_server()["is_master"]):
        thr = threading.Thread(target=delete_async, args=(file, headers), kwargs={})
        thr.start()  # will run "foo"
    return jsonify({'success': True})

class Transaction(threading.Thread):
    def __init__(self, lock, file_reference, directory_reference, cache_reference):
        threading.Thread.__init__(self)
        self.lock = lock
        self.file_reference = file_reference
        self.cache_reference = cache_reference
        self.directory_reference = directory_reference

    def run(self):
        self.lock.acquire()
        reference = db.writes.find_one({"file_reference": self.file_reference, "cache_reference": self.cache_reference})
        if (reference):
            # then, queue the write
            write_queue.put({"file_reference": self.file_reference, "cache_reference": self.cache_reference})
            self.lock.release()
            return
        self.lock.release()
        # now, write to the file on disk and Redis cache
        cache.create(self.directory_reference + "_" + self.file_reference, cache.get(self.cache_reference))
        cache.delete(self.cache_reference)
        with open(self.file_reference, "wb") as fo:
            fo.write(cache.get(self.directory_reference + "_" + self.file_reference))


class DeleteTransaction(threading.Thread):
    def __init__(self, lock, file_reference, directory_reference):
        threading.Thread.__init__(self)
        self.lock = lock
        self.file_reference = file_reference
        self.directory_reference = directory_reference

    def run(self):
        self.lock.acquire()
        if db.files.find_one({"reference": self.file_reference, "directory": self.directory_reference,
                              "server": get_current_server()["reference"]}):
            cache.delete(self.file_reference + "_" + self.directory_reference)
            os.remove(self.file_reference)
        self.lock.release()


class RollbackTransaction(threading.Thread):
    def __init__(self, lock, file_reference, directory_reference):
        threading.Thread.__init__(self)
        self.lock = lock
        self.file_reference = file_reference
        self.directory_reference = directory_reference

    def run(self):
        self.lock.acquire()
        count = 0
        server_count = get_total_servers()
        for file in db.files.find({}):
            if file.find_one({"reference": self.file_reference, "directory": self.directory_reference, "server": get_current_server()["reference"]}):
                count += 1

        if count > 0 and count/server_count <= 0.5:
            delete_transaction = DeleteTransaction(write_lock, file["reference"], directory["reference"])
            delete_transaction.start()

        self.lock.release()


class QueuedWriteHandler(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            file_write = write_queue.get()
            thread = Transaction(file_write["file_reference"], file_write["cache_reference"])
            thread.start()
            write_queue.task_done()


class Authentication:
    def __init__(self):
        pass

    @staticmethod
    def pad(s):
        return s + b"\0" * (AES.block_size - len(s) % AES.block_size)

    @staticmethod
    def encode(key, decoded):
        cipher = AES.new(key, AES.MODE_ECB)  # never use ECB in strong systems obviously
        encoded = base64.b64encode(cipher.encrypt(Authentication.pad(decoded)))
        return encoded

    @staticmethod
    def decode(key, encoded):
        cipher = AES.new(key, AES.MODE_ECB)  # never use ECB in strong systems obviously
        decoded = cipher.decrypt(base64.b64decode(encoded))
        return decoded.strip()


class Cache:
    def __init__(self, host='127.0.0.1', port=6379, db=0):
        self.host = host
        self.port = port
        self.db = db
        self.pool = None
        self.server = None

    def create_instance(self):
        self.pool = redis.ConnectionPool(host=self.host, port=self.port, db=self.db)
        self.server = redis.Redis(connection_pool=self.pool)

    def get_instance(self):
        return self.server

    def get(self, key):
        return self.server.get(key)

    def create(self, key, data):
        self.server.set(key, data)

    def delete(self, key):
        self.server.delete(key)

    def exists(self, key):
        return self.server.exists(key)

    @staticmethod
    def compress(data):
        return zlib.compress(data)

    @staticmethod
    def decompress(data):
        return zlib.decompress(data)


class File:
    def __init__(self):
        pass

    @staticmethod
    def create(name, directory_name, directory_reference, server_reference):
        m = hashlib.md5()
        m.update(directory_reference + "/" + directory_name)
        db.files.insert({"name": name
                            , "directory": directory_reference
                            , "server": server_reference
                            , "reference": m.hexdigest()
                            , "updated_at": datetime.datetime.utcnow()})
        file = db.files.find_one({"reference": m.hexdigest()})
        return file


class Directory:
    def __init__(self):
        pass

    @staticmethod
    def create(name, server):
        m = hashlib.md5()
        m.update(name)
        db.directories.insert({"name": name, "reference": m.hexdigest(), "server": server})
        directory = db.directories.find_one({"name": name, "reference": m.hexdigest()})
        return directory


cache = Cache()
cache.create_instance()

if __name__ == '__main__':
    with application.app_context():
        m = hashlib.md5()

        servers = db.servers.find()
        for server in servers:
            print(server)
            if (server['in_use'] == False):
                server['in_use'] = True
                SERVER_PORT = server['port']
                SERVER_HOST = server['host']
                queued_write_handler = QueuedWriteHandler()
                queued_write_handler.setDaemon(True)
                queued_write_handler.start()
                db.servers.update({'reference': server['reference']}, server, upsert=True)
                application.run(host=server['host'], port=server['port'])
