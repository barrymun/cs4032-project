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
Use "sudo" before any (or all) docker commands where applicable.
<br/><br/>
Ensure that you are logged in:
```bash
docker login
```

### Build the authentication_server image and generate container
Build your custom image:
```bash
docker build -t <image_name> -f docker-authserver/Dockerfile .
```
List all currently available (successfully built) images:
```bash
docker images
```
Tag the image using your docker repo:
```bash
docker tag <image_id> <username>/<repo>:latest
```
Push your custom image to your docker repo:
```bash
docker push <username>/<repo>
```
Create a container (Run the image):
<br/>
(The following command ensures a mongod daemon is created, as opposed to a standard docker run command)
```bash
docker run -p 28001:27017 --name <container_name> -d <username>/<repo> --smallfiles
```
List all currently active containers:
```bash
docker ps -s
```

### Create the container for this image
Build your custom image:
```bash
docker build -t <image_name> -f docker-dirserver/Dockerfile .
```
List all currently available (successfully built) images:
```bash
docker images
```
Tag the image using your docker repo:
```bash
docker tag <image_id> <username>/<repo>:latest
```
Push your custom image to your docker repo:
```bash
docker push <username>/<repo>
```
Create a container (Run the image):
<br/>
(The following command ensures a mongod daemon is created, as opposed to a standard docker run command)
<br/>
Let "X" below represent incrementing ports; (28002, 28003, 28004)
```bash
docker run -p <X>:27017 --name <container_name> -d <username>/<repo> --smallfiles
```
List all currently active containers:
```bash
docker ps -s
```
Please see the attached testing/commands.txt for more information on the exact commands issued.

### Run the user.py script to simulate test user interactions
```bash
python user.py
```
This python script will simulate file upload, download and delete operations and transactions.

### Miscellaneous
Refer to the "testing" directory to view screenshots of tests, the system in action, etc.
<br/><br/>
Refer to "documentation" for a detailed description of the system.