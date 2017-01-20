import hashlib
import os
import threading

class ServerTransactions:
    def upload_async_transaction(file, client_request):
        transaction = Transaction(write_lock, file['reference'], directory['reference'], pre_write_cache_reference)
        transaction.start()

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
                if r.status_code == 200:
                    TransactionStatus.create(file['reference'] + directory['reference'], server, "SUCCESS")
                else:
                    TransactionStatus.create(file['reference'] + directory['reference'], server, "FAILURE")

            if (TransactionStatus.total_success_count(file['reference'] + directory['reference'])
                    < TransactionStatus.total_success_count(file['reference'] + directory['reference'])):
                # make API request to '/server/file/rollback for all servers
                for serv in db.servers.find({}):
                    requests.post("http://" + host + ":" + port + "/server/file/delete", data='', headers=headers)

    def delete_async_transaction(client_request):
        delete_transaction = DeleteTransaction(write_lock, file["reference"], directory["reference"])
        delete_transaction.start()

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
                if r.status_code == 200:
                    TransactionStatus.create(file['reference'] + directory['reference'], server, "SUCCESS")
                else:
                    TransactionStatus.create(file['reference'] + directory['reference'], server, "FAILURE")

            if (TransactionStatus.total_success_count(file['reference'] + directory['reference'])
                    < TransactionStatus.total_success_count(file['reference'] + directory['reference'])):
                # make API request to '/server/file/rollback for all servers
                for serv in db.servers.find({}):
                    requests.post("http://" + host + ":" + port + "/server/file/delete", data='', headers=headers)


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
        for server in db.servers.find({}):
            if db.files.find_one({"reference": self.file_reference, "directory": self.directory_reference,
                                  "server": server["reference"]}):
                delete_transaction = DeleteTransaction(write_lock, file["reference"], directory["reference"])
                delete_transaction.start()


class TransactionStatus:
    def __init__(self):
        pass

    @staticmethod
    def create(name, server, status):
        m = hashlib.md5()
        m.update(name)
        transaction = db.transactions.find_one({"reference": m.hexdigest()})
        if transaction:
            transaction["ledger"][server] = status
            # update transaction in Mongo..
        else:
            db.transactions.insert({"reference": m.hexdigest(), "ledger": {server: status}})

    @staticmethod
    def get(name):
        m = hashlib.md5()
        m.update(name)
        return db.transactions.find_one({"reference": m.hexdigest()})

    @staticmethod
    def total_success_count(name):
        transaction = TransactionStatus.get(name)
        ledger = transaction["ledger"]
        count = 0
        for server_reference in ledger.iterkeys():
            if ledger[server_reference] == "SUCCESS":
                count = count + 1
        return count

    @staticmethod
    def total_failure_count(name):
        transaction = TransactionStatus.get(name)
        ledger = transaction["ledger"]
        count = 0
        for server_reference in ledger.iterkeys():
            if ledger[server_reference] == "FAILURE":
                count = count + 1
        return count

    @staticmethod
    def total_unknown_count(name):
        transaction = TransactionStatus.get(name)
        ledger = transaction["ledger"]
        count = 0
        for server_reference in ledger.iterkeys():
            if ledger[server_reference] == "UNKNOWN":
                count = count + 1
        return count
