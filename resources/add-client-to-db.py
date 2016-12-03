import datetime
import os

from flask import Flask
from flask_pymongo import PyMongo
from flask_pymongo import MongoClient

connection = MongoClient()
db = connection['dist']
db.clients.drop()

client = [{"client_id": "1"
               , "session_key": "928F767EADE2DBFD62BFCD65B8E21"
               , "session_key_expires": (datetime.datetime.utcnow() + datetime.timedelta(seconds=60 * 60 * 4)).strftime('%Y-%m-%d %H:%M:%S')
               , "public_key": "0123456789abcdef0123456789abcdef"
               , "password": "0dP1jO2zS7111111"},
           {"client_id": "2"
               , "session_key": "98D4BD8C1EAFAEA54A1D818D95BA1"
               , "session_key_expires": (datetime.datetime.utcnow() + datetime.timedelta(seconds=60 * 60 * 4)).strftime('%Y-%m-%d %H:%M:%S')
               , "public_key": "0123456789abcdef0123456789abcdef"
               , "password": "0dP1jO2zS7111111"},
           {"client_id": "3"
               , "session_key": "8A3A915849C95AC11F67DACA8EB89"
               , "session_key_expires": (datetime.datetime.utcnow() + datetime.timedelta(seconds=60 * 60 * 4)).strftime('%Y-%m-%d %H:%M:%S')
               , "public_key": "0123456789abcdef0123456789abcdef"
               , "password": "0dP1jO2zS7111111"},
           {"client_id": "4"
               , "session_key": "CC6C95A928319BFC816BEDF2A2BBC"
               , "session_key_expires": (datetime.datetime.utcnow() + datetime.timedelta(seconds=60 * 60 * 4)).strftime('%Y-%m-%d %H:%M:%S')
               , "public_key": "0123456789abcdef0123456789abcdef"
               , "password": "0dP1jO2zS7111111"},
           {"client_id": "5"
               , "session_key": "751C792CB49DF4C859E6F4F3A1EFA"
               , "session_key_expires": (datetime.datetime.utcnow() + datetime.timedelta(seconds=60 * 60 * 4)).strftime('%Y-%m-%d %H:%M:%S')
               , "public_key": "0123456789abcdef0123456789abcdef"
               , "password": "0dP1jO2zS7111111"}]

clients = db.clients
clients.insert(client)