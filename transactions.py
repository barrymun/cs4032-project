import TransactionStatus

from dirserver import Transaction
from dirserver import TransactionStatus


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
