
FROM ubuntu:14.04

FROM python:2.7

RUN apt-get update && apt-get install -y \
    apt-utils -y \
    php5-mcrypt \
    mongodb \
    python-pip \
    libcurl3 \
    libcurl3-dev \
    php5-curl \
    python-dev \
    python-requests


RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 0C49F3730359A14518585931BC711F9BA15703C6

RUN echo "deb [ arch=amd64 ] http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.4 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-3.4.list

RUN apt-get update && \

    apt-get --reinstall install -y mongodb && \

    apt-get install -y sudo && \

    pip install Flask && \

    pip install pyfscache && \

    pip install Flask-PyMongo && \

    pip install pycrypto

RUN mkdir -p /data/db

EXPOSE 27017

RUN sudo service mongodb start && \

    sudo service mongodb status

COPY transactions.py /src/transactions.py
COPY dirserver.py /src/dirserver.py

CMD ["python","/src/dirserver.py"]