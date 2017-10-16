#!flask/bin/python
from flask import Flask
from flask_jsonrpc import JSONRPC
import openstackmethods as opm
import os

conn=None
app = Flask(__name__)
jsonrpc = JSONRPC(app, '/api')

def check_auth(username, password):
        global conn
        conn=opm.create_connection(username,password)
        try:
            conn.authorize()
            return True
        except Exception:
            return False

@jsonrpc.method('App.index', authenticated=check_auth)
def index():
    return u'Connected'
@jsonrpc.method('App.createServer', authenticated=check_auth)
def createServer(username2,servername, keyname):
    try :
        opm.create_server(conn, username2, servername, keyname)
        return " Created Server"
    except Exception as e:
        return "Server with name " + servername + " already existing"
@jsonrpc.method('App.deleteServer', authenticated=check_auth)

def deleteServer(servername):
    opm.delete_server(conn,servername)
    return " Deleted Server"

@jsonrpc.method('App.stopServer', authenticated=check_auth)
def stopServer(servername):
    feedback= opm.stop_server(conn,servername)
    return feedback

@jsonrpc.method('App.pauseServer', authenticated=check_auth)
def pauseServer(servername):
    feedback= opm.pause_server(conn,servername)
    return feedback

@jsonrpc.method('App.unPauseServer', authenticated=check_auth)
def unPauseServer(servername):
    feedback= opm.unpause_server(conn,servername)
    return feedback


@jsonrpc.method('App.addFloatingIPtoServer', authenticated=check_auth)
def add_floating_ip_to_Server(servername):
    feedback=opm.add_floating_ip_to_server(conn,servername)
    return feedback

if __name__ == '__main__':
    app.run(debug=True)