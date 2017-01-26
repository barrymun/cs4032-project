
FROM ubuntu:16.04

MAINTAINER Docker

RUN apt-get update && apt-get -y upgrade && apt-get install -y \
    python \
    python-distribute \
    python-pip \
    libcurl3 \
    libcurl3-dev \
    python-dev


RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927
RUN echo "deb http://repo.mongodb.org/apt/ubuntu $(cat /etc/lsb-release | grep DISTRIB_CODENAME | cut -d= -f2)/mongodb-org/3.2 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-3.2.list

RUN apt-get update && \

    apt-get install -y mongodb-org && \

    apt-get install -y python3-pip


RUN pip install Flask && \

    pip install pyfscache && \

    pip install Flask-PyMongo && \

    pip install pycrypto && \

    pip install --upgrade setuptools

RUN mkdir -p /data/db

EXPOSE 27017

ENTRYPOINT ["/usr/bin/mongod"]

COPY transactions.py /src/transactions.py
COPY dirserver.py /src/dirserver.py

CMD ["python","/src/dirserver.py"]