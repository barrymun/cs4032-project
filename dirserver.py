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


def get_total_servers():
    with application.app_context():
        return count(db.servers.find({}))


def decode(key, encoded):
    cypher = AES.new(key, AES.MODE_ECB)
    decyphered = cypher.decrypt(base64.b64decode(encoded))
    return decyphered.strip()


@application.route('/f/download', methods=['POST'])
def download():
    data = request.get_json(force=True)
    filename = data.get('filename')
    dir_ref = data.get('directory')
    m_digest = hashlib.md5()
    m_digest.update(dir_ref)
    directory = db.directories.find_one(
        {"name": dir_ref, "reference": m_digest.hexdigest(), "server": server_instance()["reference"]})
    if not directory:
        return jsonify({"success": False})

    file = db.files.find_one(
        {"name": filename, "directory": directory['reference'], "server": server_instance()["reference"]})
    if not file:
        return jsonify({"success": False})


@application.route('/f/upload', methods=['POST'])
def upload():
    headers = request.headers
    file_hash = headers['filename']
    directory_name_encoded = headers['directory']
    access_key = headers['access_key']
    s_id = decode(AUTH_KEY, access_key).strip()
    dir_ref = decode(s_id, directory_name_encoded)
    filename = decode(s_id, file_hash)
    m_digest = hashlib.md5()
    m_digest.update(dir_ref)
    if not db.directories.find_one(
            {"name": dir_ref, "reference": m_digest.hexdigest(), "server": server_instance()["reference"]}):
        m_digest = hashlib.md5()
        m_digest.update(dir_ref)
        db.directories.insert({"name": dir_ref
                                  , "reference": m_digest.hexdigest()
                                  , "server": server_instance()["reference"]})
        directory = db.directories.find_one(
            {"name": dir_ref, "reference": m_digest.hexdigest(), "server": server_instance()["reference"]})
    else:
        directory = db.directories.find_one(
            {"name": dir_ref, "reference": m_digest.hexdigest(), "server": server_instance()["reference"]})

    if not db.files.find_one(
            {"name": filename, "directory": directory['reference'], "server": server_instance()["reference"]}):
        m_digest = hashlib.md5()
        m_digest.update(directory['reference'] + "/" + directory['name'])
        db.files.insert({"name": filename
                            , "directory": directory['reference']
                            , "server": server_instance()["reference"]
                            , "reference": m_digest.hexdigest()
                            , "updated_at": datetime.datetime.utcnow()})
        file = db.files.find_one(
            {"name": filename, "directory": directory['reference'], "server": server_instance()["reference"]})
    else:
        file = db.files.find_one(
            {"name": filename, "directory": directory['reference'], "server": server_instance()["reference"]})

    if (server_instance()["master_server"]):
        thr = threading.Thread(target=upload_async, args=(file, headers), kwargs={})
        thr.start()
    return jsonify({'success': True})


@application.route('/f/delete', methods=['POST'])
def delete():
    headers = request.headers
    directory_name_encoded = headers['directory']
    filename_encoded = headers['filename']
    access_key = headers['access_key']
    s_id = decode(AUTH_KEY, access_key).strip()
    dir_ref = decode(s_id, directory_name_encoded)
    filename = decode(s_id, filename_encoded)
    m_digest = hashlib.md5()
    m_digest.update(dir_ref)
    server = server_instance()
    print(server)
    if not db.directories.find_one(
            {"name": dir_ref, "reference": m_digest.hexdigest(), "server": server_instance()["reference"]}):
        print("No directory found")
        return jsonify({"success": False})
    else:
        directory = db.directories.find_one(
            {"name": dir_ref, "reference": m_digest.hexdigest(), "server": server_instance()["reference"]})
    file = db.files.find_one(
        {"name": filename, "directory": directory['reference'], "server": server_instance()["reference"]})
    if not file:
        print("No file found")
        return jsonify({"success": False})

    if (server_instance()["master_server"]):
        thr = threading.Thread(target=delete_async, args=(file, headers), kwargs={})
        thr.start()
    return jsonify({'success': True})


class QHandler(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            file_write = write_queue.get()
            thread = Transaction(file_write["file_reference"], file_write["cache_reference"])
            thread.start()
            write_queue.task_done()


if __name__ == '__main__':
    with application.app_context():
        m_digest = hashlib.md5()
        servers = db.servers.find()
        for s in servers:
            print(s)
            if (s['in_use'] == False):
                s['in_use'] = True
                SERVER_PORT = s['port']
                SERVER_HOST = s['host']
                q_handler = QHandler()
                q_handler.setDaemon(True)
                q_handler.start()
                db.servers.update({'reference': s['reference']}, s, upsert=True)
                application.run(host=s['host'], port=s['port'])
