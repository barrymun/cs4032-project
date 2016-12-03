import base64
import md5
import datetime
import json
import hashlib
import flask
import os
from flask import Flask
from flask import request
from flask import jsonify
from flask import Response
from flask.ext.pymongo import PyMongo

application = Flask(__name__)
mongo = PyMongo(application)

# constants
AUTH_SERVER_STORAGE_SERVER_KEY = "d41d8cd98f00b204e9800998ecf8427e"

def reset():
    db = mongo.db.server
    db.directories.drop()
    db.files.drop()

@application.route('/server/file/upload', methods=['POST'])
def file_upload():
    data = request.get_data()
    headers = request.headers
    filename = headers['filename']
    directory_name = headers['directory']

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

    return jsonify({'success':True})


@application.route('/server/file/download', methods=['POST'])
def file_download():
    data = request.get_json(force=True)
    ticket = data.get('auth_token')
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
    return jsonify({"success":True})


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