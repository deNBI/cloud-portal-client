#!flask/bin/python
from flask import Flask
from flask_jsonrpc import JSONRPC
from flask_jsonrpc.exceptions import InvalidCredentialsError
import openstackmethods as opm
import os
import configparser

conn=None
app = Flask(__name__)
jsonrpc = JSONRPC(app, '/api')
config=configparser.ConfigParser()
config.read('config.cfg')
NETWORK=config.get('Connection','network')
USERNAME=config.get('Connection','username')
PASSWORD=config.get('Connection','password')
AUTH_URL=config.get('Connection','auth_url')
PROJECT_NAME=config.get('Connection','project_name')
USER_DOMAIN_NAME=config.get('Connection','user_domain_name')
PROJECT_DOMAIN_NAME=config.get('Connection','project_domain_name')

def check_auth():
        global conn
        conn=opm.create_connection(username=USERNAME,password=PASSWORD,auth_url=AUTH_URL,project_domain_name=PROJECT_DOMAIN_NAME,user_domain_name=USER_DOMAIN_NAME,project_name=PROJECT_NAME)
        try:
            conn.authorize()
            return True
        except Exception:
            return False

@jsonrpc.method('App.index')
def index():
    if check_auth() is True:
     return u'Connected'
    else:
        raise  InvalidCredentialsError()
@jsonrpc.method('App.createServer')
def createServer(servername, keyname,imagename,flavorname):
    if check_auth() is True:
        try :
            feedback=opm.create_server(conn, servername, keyname,imagename,flavorname,NETWORK,USERNAME)
            return feedback
        except Exception as e:
            return e
    else:
        raise  InvalidCredentialsError()
@jsonrpc.method('App.deleteServer')

def deleteServer(servername):
    if check_auth() is True:
        opm.delete_server(conn,servername)
        return " Deleted Server"
    else:
        raise InvalidCredentialsError()

@jsonrpc.method('App.stopServer')
def stopServer(servername):
    if check_auth() is True:
        feedback= opm.stop_server(conn,servername)
        return feedback
    else:
        raise InvalidCredentialsError()

@jsonrpc.method('App.pauseServer')
def pauseServer(servername):
    if check_auth() is True:
        feedback= opm.pause_server(conn,servername)
        return feedback
    else:
        raise InvalidCredentialsError()
@jsonrpc.method('App.unPauseServer')
def unPauseServer(servername):
    if check_auth() is True:
        feedback= opm.unpause_server(conn,servername)
        return feedback
    else:
        raise InvalidCredentialsError()

@jsonrpc.method('App.addFloatingIPtoServer')
def add_floating_ip_to_Server(servername):
    if check_auth() is True:
        feedback=opm.add_floating_ip_to_server(conn,servername)
        return feedback
    else:
        raise InvalidCredentialsError()
@jsonrpc.method('App.getFlavors')
def get_flavors():
    if check_auth() is True:
        feedback=opm.get_flavors(conn)
        return feedback
    else:
        raise InvalidCredentialsError()
@jsonrpc.method('App.getImages')
def get_images():
    if check_auth() is True:
        feedback=opm.get_images(conn)
        return feedback
    else:
        raise InvalidCredentialsError()
@jsonrpc.method('App.getServers')
def get_servers():
    if check_auth() is True:
        feedback=opm.get_servers(conn)
        return feedback
    else:
        raise InvalidCredentialsError()
if __name__ == '__main__':
    app.run(debug=True)