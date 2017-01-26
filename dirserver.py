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
mongo_server = "127.0.0.1"
mongo_port = "27017"
connect_string = "mongodb://" + mongo_server + ":" + mongo_port
connection = MongoClient(connect_string)
db = connection.project
servers = db.servers
server_transactions = ServerTransactions()
AUTH_SERVER_STORAGE_SERVER_KEY = "17771fab5708b94b42cfd00c444b6eaa"
SERVER_HOST = None
SERVER_PORT = None


def reset():
    db.directories.drop()
    db.files.drop()
    db.transactions.drop()


def upload_async(file, client_request):
    server_transactions.upload_async_trans(file, client_request)


def delete_async(client_request):
    server_transactions.delete_async_transaction(client_request)


def get_current_server():
    with application.app_context():
        return db.servers.find_one({"host": SERVER_HOST, "port": SERVER_PORT})


def get_total_servers():
    with application.app_context():
        return count(db.servers.find({}))


def decode(key, encoded):
    cypher = AES.new(key, AES.MODE_ECB)
    decyphered = cypher.decrypt(base64.b64decode(encoded))
    return decyphered.strip()


@application.route('/server/file/upload', methods=['POST'])
def file_upload():
    # Need to update cached record (if exists)
    # pre_write_cache_reference = uuid.uuid4()
    # print(Cache.compress(request.get_data()))
    # cache.create(pre_write_cache_reference, Cache.compress(request.get_data()))
    # print cache.get(pre_write_cache_reference)

    headers = request.headers
    filename_encoded = headers['filename']
    directory_name_encoded = headers['directory']
    ticket = headers['ticket']
    session_key = decode(AUTH_SERVER_STORAGE_SERVER_KEY, ticket).strip()
    directory_name = decode(session_key, directory_name_encoded)
    filename = decode(session_key, filename_encoded)
    m = hashlib.md5()
    m.update(directory_name)

    if not db.directories.find_one(
            {"name": directory_name, "reference": m.hexdigest(), "server": get_current_server()["reference"]}):
        m = hashlib.md5()
        m.update(directory_name)
        db.directories.insert({"name": directory_name
                                  , "reference": m.hexdigest()
                                  , "server": get_current_server()["reference"]})
        directory = db.directories.find_one(
            {"name": directory_name, "reference": m.hexdigest(), "server": get_current_server()["reference"]})
    else:
        directory = db.directories.find_one(
            {"name": directory_name, "reference": m.hexdigest(), "server": get_current_server()["reference"]})

    if not db.files.find_one(
            {"name": filename, "directory": directory['reference'], "server": get_current_server()["reference"]}):
        m = hashlib.md5()
        m.update(directory['reference'] + "/" + directory['name'])
        db.files.insert({"name": filename
                            , "directory": directory['reference']
                            , "server": get_current_server()["reference"]
                            , "reference": m.hexdigest()
                            , "updated_at": datetime.datetime.utcnow()})
        file = db.files.find_one(
            {"name": filename, "directory": directory['reference'], "server": get_current_server()["reference"]})
    else:
        file = db.files.find_one(
            {"name": filename, "directory": directory['reference'], "server": get_current_server()["reference"]})

    if (get_current_server()["is_master"]):
        thr = threading.Thread(target=upload_async, args=(file, headers), kwargs={})
        thr.start()  # will run "foo"
    return jsonify({'success': True})


@application.route('/server/file/delete', methods=['POST'])
def file_delete():
    headers = request.headers
    filename_encoded = headers['filename']
    directory_name_encoded = headers['directory']
    ticket = headers['ticket']
    session_key = decode(AUTH_SERVER_STORAGE_SERVER_KEY, ticket).strip()
    directory_name = decode(session_key, directory_name_encoded)
    filename = decode(session_key, filename_encoded)
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

    if (get_current_server()["is_master"]):
        thr = threading.Thread(target=delete_async, args=(file, headers), kwargs={})
        thr.start()  # will run "foo"
    return jsonify({'success': True})


@application.route('/server/file/download', methods=['POST'])
def file_download():
    data = request.get_json(force=True)
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

        # cache_file_reference = directory['reference'] + "_" + file['reference']
        # if cache.check(cache_file_reference):
        #     return Cache.decompress(cache.get(cache_file_reference))
        # else:
        #     return flask.send_file(file["reference"])


class QueuedWriteHandler(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            file_write = write_queue.get()
            thread = Transaction(file_write["file_reference"], file_write["cache_reference"])
            thread.start()
            write_queue.task_done()


# cache = Cache('/tmp/mycachedir')

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
