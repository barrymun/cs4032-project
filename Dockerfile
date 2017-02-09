
FROM ubuntu:14.04

RUN sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10 \
  && echo "deb http://downloads-distro.mongodb.org/repo/debian-sysvinit dist 10gen" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.0.list \
  && apt-get update && apt-get -q -y install \
    nodejs\
    npm \
    git \
    mongodb-org

CMD ["mongod", "--dbpath", "."]