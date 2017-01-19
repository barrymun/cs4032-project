import threading

class ServerTransactions:

    def upload_async_transaction(file, client_request):
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
                return r


    def delete_async_transaction(client_request):
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
                return r


    def rollback_async_transaction(client_request):
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
                return r