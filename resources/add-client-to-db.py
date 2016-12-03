import datetime

from flask.ext.pymongo import Connection

connection = Connection()
db = connection['dist']
collection = db['client']

clients = [{"client_id": "1"
    ,"session_key": "928F767EADE2DBFD62BFCD65B8E21"
    ,"session_key_expires": (datetime.utcnow() + timedelta(seconds=60*5)).strftime('%Y-%m-%d %H:%M:%S')
    ,"public_key": "6EC46E3DC79A2D4DBE79151C2DCE1"
    ,"password": "0dP1jO2zS7"},
    {"client_id": "2"
    ,"session_key": "98D4BD8C1EAFAEA54A1D818D95BA1"
    ,"session_key_expires": (datetime.utcnow() + timedelta(seconds=60*5)).strftime('%Y-%m-%d %H:%M:%S')
    ,"public_key": "D9EEE7B719786189C6F449BBE9714"
    ,"password": "GhN9bZnouL"},
    {"client_id": "3"
    ,"session_key": "8A3A915849C95AC11F67DACA8EB89"
    ,"session_key_expires": (datetime.utcnow() + timedelta(seconds=60*5)).strftime('%Y-%m-%d %H:%M:%S')
    ,"public_key": "6EAF254F31C1D1B91766CFBFAC928"
    ,"password": "f9C1731KLs"},
    {"client_id": "4"
    ,"session_key": "CC6C95A928319BFC816BEDF2A2BBC"
    ,"session_key_expires": (datetime.utcnow() + timedelta(seconds=60*5)).strftime('%Y-%m-%d %H:%M:%S')
    ,"public_key": "DA73157ACAB711738E179BE5F8392"
    ,"password": "P6ugR77H5P"},
    {"client_id": "5"
    ,"session_key": "751C792CB49DF4C859E6F4F3A1EFA"
    ,"session_key_expires": (datetime.utcnow() + timedelta(seconds=60*5)).strftime('%Y-%m-%d %H:%M:%S')
    ,"public_key": "6E9B98EE737127C561725E16B36A2"
    ,"password": "b0lp6ia30I"}]

clients = db.posts
posts.insert(clients)
