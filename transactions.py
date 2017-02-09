import hashlib
import os
import threading

import requests
from diskcache import Cache
from flask import Flask
from flask_pymongo import PyMongo
from pymongo import MongoClient

thread_lock = threading.Lock()
SERVER_RESPONSE_POS = 200
application = Flask(__name__)
mongo = PyMongo(application)
mongo_server = "localhost"
mongo_port = "27017"
str = "mongodb://" + mongo_server + ":" + mongo_port
connection = MongoClient(str)
db = connection.project
AUTH_KEY = "17771fab5708b94b42cfd00c444b6eaa"
SERVER_HOST = None
SERVER_PORT = None

# Set the cache instance
cache = Cache('/tmp/mycachedir')


def get_current_server(host, port):
    with application.app_context():
        return db.servers.find_one({"host": host, "port": port})


class ServerTransactions:
    def asynchronous_upload_transaction(self, file, directory, headers):

        with application.app_context():
            servers = db.servers.find()
            for server in servers:
                host = server["host"]
                port = server["port"]
                transaction = Transaction(thread_lock, file, directory)
                transaction.start()

                cache_hash = file + "/" + directory + "/" + server['identifier']
                # None is tacked on at the end here - needs further investigation
                data = cache.get(cache_hash)
                #print data

                if get_current_server(host, port)['master_server']:
                    continue

                if (host == SERVER_HOST and port == SERVER_PORT):
                    continue

                with open(file, "wb") as f:
                    f.write(data)
                print(headers)

                headers = {'access_key': headers['access_key'],
                           'directory': headers['directory'],
                           'filename': headers['filename']}
                r = requests.post("http://" + host + ":" + port + "/file/upload", data=data, headers=headers)

                if r.status_code == SERVER_RESPONSE_POS:
                    TransactionStatus.create(file + directory, server, "SUCCESS")
                else:
                    TransactionStatus.create(file + directory, server, "FAILURE")

            if (TransactionStatus.total_success_count()
                    >= TransactionStatus.total_failure_count()
                    + TransactionStatus.total_unknown_count()):
                requests.post("http://" + host + ":" + port + "/file/delete", data='', headers=headers)

    def asynchronous_delete_transaction(self, file, directory, headers):

        with application.app_context():
            servers = db.servers.find()
            for server in servers:
                host = server["host"]
                port = server["port"]
                delete_transaction = DeleteTransaction(thread_lock, file, directory, host, port)
                delete_transaction.start()

                if get_current_server(host, port)['master_server']:
                    continue

                if (host == SERVER_HOST and port == SERVER_PORT):
                    continue
                print(headers)
                headers = {'access_key': headers['access_key'],
                           'directory': headers['directory'],
                           'filename': headers['filename']}
                r = requests.post("http://" + host + ":" + port + "/file/delete", data='', headers=headers)

                if r.status_code == SERVER_RESPONSE_POS:
                    TransactionStatus.create(file + directory, server, "SUCCESS")
                else:
                    TransactionStatus.create(file + directory, server, "FAILURE")
            if (TransactionStatus.total_success_count()
                    >= TransactionStatus.total_failure_count()
                    + TransactionStatus.total_unknown_count()):
                requests.post("http://" + host + ":" + port + "/file/delete", data='', headers=headers)


class Transaction(threading.Thread):
    def __init__(self, lock, filename, directory):
        threading.Thread.__init__(self)
        self.lock = lock
        self.filename = filename
        self.directory = directory

    def run(self):
        self.lock.acquire()
        return
        self.lock.release()


class DeleteTransaction(threading.Thread):
    def __init__(self, lock, filename, directory, host, port):
        threading.Thread.__init__(self)
        self.lock = lock
        self.filename = filename
        self.directory = directory
        self.host = host
        self.port = port

    def run(self):
        self.lock.acquire()
        if db.files.find_one({"identifier": self.filename, "directory": self.directory,
                              "server": get_current_server(self.host, self.port)}):
            db.files.remove({"identifier": self.filename, "directory": self.directory,
                             "server": get_current_server(self.host, self.port)})
            os.remove(self.filename)
        self.lock.release()


# This will be used to monitor the "health" of any active servers
class TransactionStatus:
    def __init__(self):
        pass

    @staticmethod
    def create(name, server, status):
        hash_key = hashlib.md5()
        hash_key.update(name)
        transaction = db.transactions.find_one({"identifier": hash_key.hexdigest()})
        if transaction:
            transaction["ledger"] = status
        else:
            db.transactions.insert(
                {"identifier": hash_key.hexdigest(), "ledger": status, "server-identifier": server['identifier']})

    @staticmethod
    def get(name):
        hash_key = hashlib.md5()
        hash_key.update(name)
        return db.transactions.find_one({"identifier": hash_key.hexdigest()})

    @staticmethod
    def total_success_count():
        count = 0
        for transaction in db.transactions.find():
            if transaction['ledger'] == "SUCCESS":
                count += 1
        return count

    @staticmethod
    def total_failure_count():
        count = 0
        for transaction in db.transactions.find():
            if transaction['ledger'] == "FAILURE":
                count += 1
        return count

    @staticmethod
    def total_unknown_count():
        count = 0
        for transaction in db.transactions.find():
            if transaction['ledger'] == "UNKNOWN":
                count += 1
        return count
