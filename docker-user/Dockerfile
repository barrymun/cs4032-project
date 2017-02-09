FROM       ubuntu:16.04
MAINTAINER Docker

RUN apt-get update && apt-get install -y \
    apt-utils -y \
    python-pip \
    libcurl3 \
    libcurl3-dev \
    python-dev \
    python-requests

RUN pip install --upgrade pip && \
    pip install Flask && \
    pip install pyfscache && \
    pip install Flask-PyMongo && \
    pip install pycrypto

COPY user.py /src/user.py

CMD ["python","/src/user.py"]