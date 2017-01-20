# Setting up the Distributed File System: (WITHOUT DOCKER)

## Run the setup file. This will create all the required mongodb collections

```bash
python setup.py
```

A master_server is also created, and managed by the mongodb. All newly created master servers **must** be added to that collection in the db.

## Next, the authentication server must be initialised.

```bash
python auth-server.py
```

This will ensure that clients can be managed through creation **and** authentication.

## Create the worker servers, named dirserver in this instance. Create as many is required.

```bash
python dirserver.py
```

Run the above as many times as required, in new windows of course.

## Finally, run the test client to ensure that the requests are handled by the worker servers, and the master_server manages these instances correctly.

```bash
python client.py
```

# Setting up the Distributed File System: (WITH DOCKER)

WIP