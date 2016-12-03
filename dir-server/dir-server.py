import base64
import md5
import datetime
import json

from flask import Flask
from flask import request
from flask import jsonify
from flask_pymongo import PyMongo

application = Flask(__name__)
mongo = PyMongo(application)

# constants
AUTH_SERVER_STORAGE_SERVER_KEY = "d41d8cd98f00b204e9800998ecf8427e"


@application.route('/server/file/upload', methods=['POST'])
def file_upload():
    data = request.get_data()
    headers = request.headers
    filename = headers['filename']
    directory_name = headers['directory']

    db = mongo.db.server
    directory = None
    if not db.directories.find({"name": directory_name,"reference": md5(directory_name).hexdigest()}):
        directory = Directory.create(directory_name)

    file = None
    if not db.files.find({"name": filename, "directory": directory['reference']}):
        file = File.create(filename, directory['name'], directory['reference'])

    with open(file["reference"], "wb") as fo:
        fo.write(data)

    return jsonify({'success':True})


@application.route('/server/file/download', methods=['POST'])
def file_download():
    pass

class File:
    def __init__(self):
        pass

    @staticmethod
    def create(name, directory_name, directory_reference):
        db = mongo.db.server
        file = db.files.insert({"name":name,
            "directory": directory_reference,
            "reference": md5(directory_reference + "/" + directory_name).hexdigest(),
            "updated_at": datetime.datetime.utcnow()
        })
        return file

class Directory:
    def __init__(self):
        pass

    @staticmethod
    def create(name):
        db = mongo.db.server
        db.directories.insert({"name":name
            ,"reference": md5(name).hexdigest()
        })

if __name__ == '__main__':
    application.run(host='127.0.0.1',port=8093)