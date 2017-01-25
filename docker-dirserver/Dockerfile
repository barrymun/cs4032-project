
FROM ubuntu:14.04

RUN apt-get update && apt-get install -y \
    php5-mcrypt \
    python-pip \
    libcurl3 \
    libcurl3-dev \
    php5-curl

RUN pip install Flask

COPY dirserver.py /src/dirserver.py

CMD ["python","/src/dirserver.py"]
