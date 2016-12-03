import datetime

from flask import Flask
from flask_pymongo import MongoClient

connection = MongoClient()
db = connection['dist']
collection = db['client']

client = [{"client_id": "1"
               , "session_key": "928F767EADE2DBFD62BFCD65B8E21"
               , "session_key_expires": (datetime.datetime.utcnow() + datetime.timedelta(seconds=60 * 60 * 4)).strftime('%Y-%m-%d %H:%M:%S')
               , "public_key": "2c2f415f72445943564d3d445d543b4173242d557e5b763126594e522f616f7a21243b3252412b28552e2647254369212d7c29457b714a3e2071"
               , "password": "0dP1jO2zS7"},
           {"client_id": "2"
               , "session_key": "98D4BD8C1EAFAEA54A1D818D95BA1"
               , "session_key_expires": (datetime.datetime.utcnow() + datetime.timedelta(seconds=60 * 60 * 4)).strftime('%Y-%m-%d %H:%M:%S')
               , "public_key": "79797363464a27276c204d4e23277d755941654a5323563023382a633e7548673a422d61274e7e28223a247a3949535178677c666a22302f4a69"
               , "password": "GhN9bZnouL"},
           {"client_id": "3"
               , "session_key": "8A3A915849C95AC11F67DACA8EB89"
               , "session_key_expires": (datetime.datetime.utcnow() + datetime.timedelta(seconds=60 * 60 * 4)).strftime('%Y-%m-%d %H:%M:%S')
               , "public_key": "4b77627241483c6c5e27705c73254d7428266e7d72764b536d27636568667b5157436c2339612820336c33287b212f5c244a754856273540292a"
               , "password": "f9C1731KLs"},
           {"client_id": "4"
               , "session_key": "CC6C95A928319BFC816BEDF2A2BBC"
               , "session_key_expires": (datetime.datetime.utcnow() + datetime.timedelta(seconds=60 * 60 * 4)).strftime('%Y-%m-%d %H:%M:%S')
               , "public_key": "5e2e306b4e6334486b4924436547245c345d677671283651283d627d6d5533505b71553d56502b684e38474559252022477d3f5659292f736d4f"
               , "password": "P6ugR77H5P"},
           {"client_id": "5"
               , "session_key": "751C792CB49DF4C859E6F4F3A1EFA"
               , "session_key_expires": (datetime.datetime.utcnow() + datetime.timedelta(seconds=60 * 60 * 4)).strftime('%Y-%m-%d %H:%M:%S')
               , "public_key": "396a634b34682a613e464e745c50587176415870726845504c755c75345f4d5428502c475a6950376f252263774169354c2e2459264c74327a5e"
               , "password": "b0lp6ia30I"}]

clients = db.clients
clients.insert(client)
