
FROM centos

RUN curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"

RUN python get-pip.py && \

    pip install Flask && \

    pip install Flask-PyMongo && \

    yum install -y gcc && \

    yum install -y libffi-devel && \

    yum install -y python-devel && \

    yum install -y openssl-devel && \

    pip install pycrypto

COPY auth-server.py /src/auth-server.py

CMD ["python","/src/auth-server.py"]
