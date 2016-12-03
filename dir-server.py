import base64
import md5
import datetime
import json
import hashlib
import flask
import os
import threading
import requests
from flask import Flask
from flask import request
from flask import jsonify
from flask import Response
from flask.ext.pymongo import PyMongo
from Crypto.Cipher import AES

application = Flask(__name__)
mongo = PyMongo(application)

# constants
AUTH_SERVER_STORAGE_SERVER_KEY = "d41d8cd98f00b204e9800998ecf8427e"

def reset():
    db = mongo.db.server
    db.directories.drop()
    db.files.drop()

def upload_async(file, client_request):
    with application.app_context():
        db = mongo.db.server
        servers = db.servers.find()
        for server in servers:
            host = server["host"]
            port = server["port"]
            # make POST request to upload file to server, using
            # same client request
            data = open(file['reference'], 'rb').read()

            headers = {'ticket': client_request['ticket'],
                       'directory': client_request['directory'],
                       'filename': client_request['filename']}
            r = requests.post("http://" + host + ":" + port + "/server/file/upload", data=data,
                              headers=headers)


def delete_async(file):
    with application.app_context():
        db = mongo.db.server
        servers = db.servers.find()
        for server in servers:
            host = server["host"]
            port = server["port"]
            # make POST request to delete file from server, using
            # same client request

@application.route('/server/file/upload', methods=['POST'])
def file_upload():
    data = request.get_data()
    headers = request.headers

    filename_encoded = headers['filename']
    directory_name_encoded = headers['directory']
    ticket = headers['ticket']
    session_key = Authentication.decode(AUTH_SERVER_STORAGE_SERVER_KEY, ticket).strip()
    directory_name = Authentication.decode(session_key, directory_name_encoded)
    filename = Authentication.decode(session_key, filename_encoded)

    m = hashlib.md5()
    m.update(directory_name)
    if not mongo.db.server.directories.find_one({"name": directory_name, "reference": m.hexdigest()}):
        directory = Directory.create(directory_name)
    else:
        directory = mongo.db.server.directories.find_one({"name": directory_name, "reference": m.hexdigest()})

    if not mongo.db.server.files.find_one({"name": filename, "directory": directory['reference']}):
        file = File.create(filename, directory['name'], directory['reference'])
    else:
        file = mongo.db.server.files.find_one({"name": filename, "directory": directory['reference']})
    with open(file["reference"], "wb") as fo:
        fo.write(data)
    thr = threading.Thread(target=upload_async, args=(file, {}), kwargs={})
    thr.start()  # will run "foo"
    return jsonify({'success':True})


@application.route('/server/file/download', methods=['POST'])
def file_download():
    data = request.get_json(force=True)
    authentication = data.get('authentication')

    filename = data.get('filename')
    directory_name = data.get('directory')

    m = hashlib.md5()
    m.update(directory_name)
    directory = mongo.db.server.directories.find_one({"name": directory_name, "reference": m.hexdigest()})
    if not directory:
        return jsonify({"success":False})

    file = mongo.db.server.files.find_one({"name": filename, "directory": directory['reference']})
    if not file:
        return jsonify({"success":False})

    return flask.send_file(file["reference"])

@application.route('/server/file/delete', methods=['POST'])
def file_delete():
    data = request.get_json(force=True)
    ticket = data.get('auth_token')
    filename = data.get('filename')
    directory_name = data.get('directory')

    m = hashlib.md5()
    m.update(directory_name)
    directory = mongo.db.server.directories.find_one({"name": directory_name, "reference": m.hexdigest()})
    if not directory:
        return jsonify({"success": False})

    file = mongo.db.server.files.find_one({"name": filename, "directory": directory['reference']})
    if not file:
        return jsonify({"success": False})

    os.remove(file["reference"])
    pool.apply_async(delete_async, [file, {}], None)
    return jsonify({"success":True})


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




class File:
    def __init__(self):
        pass

    @staticmethod
    def create(name, directory_name, directory_reference):
        db = mongo.db.server
        m = hashlib.md5()
        m.update(directory_reference + "/" + directory_name)
        db.files.insert({"name":name,
                                "directory":directory_reference,
                                "reference": m.hexdigest(),
                                "updated_at": datetime.datetime.utcnow()})
        file = db.files.find_one({"reference":m.hexdigest()})
        return file

class Directory:
    def __init__(self):
        pass

    @staticmethod
    def create(name):
        db = mongo.db.server
        m = hashlib.md5()
        m.update(name)
        db.directories.insert({"name":name, "reference": m.hexdigest()})
        directory = db.directories.find_one({"name":name, "reference": m.hexdigest()})
        return directory


if __name__ == '__main__':
    application.run(host='127.0.0.1',port=8093)