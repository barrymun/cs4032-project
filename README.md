# Setting up the Distributed File System: (WITHOUT DOCKER)

## first, the authentication server must be initialised.

```bash
python authenticationserver.py
```

A master_server is also created, and managed by the mongodb. All newly created master servers **must** be added to that collection in the db.

This will ensure that clients can be managed through creation **and** authentication.

## Create the worker servers, named dirserver in this instance.

```bash
python directoryserver.py
```

Run the above three times. One master_server will be created.

The authentication server can be modified to allow for more than 3 instances, but this is the number that has been selected for testing purposes.

## Finally, run the test user to ensure that the requests are handled by the worker servers, and the master_server manages these instances correctly.

```bash
python user.py
```

# Setting up the Distributed File System: (WITH DOCKER)

### Build the auth-server image

```bash
docker build -t authserver .
```

### Create the container for this image

```bash
docker run authserver
```

### Build the directory server image (2 required)

```bash
docker build -t dirserver1 -f docker-dirserver/Dockerfile .
```

```bash
docker build -t dirserver2 -f docker-dirserver/Dockerfile .
```

### Create the containers for both of these images

```bash
docker run dirserver1
```

```bash
docker run dirserver2
```

### Run the user.py script to simulate test user interactions

```bash
python user.py
```