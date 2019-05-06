import os
import sys

try:
    from VirtualMachineService import Client, Processor
except Exception:
    from .VirtualMachineService import Client, Processor

try:
    from VirtualMachineHandler import VirtualMachineHandler
except Exception:
    from .VirtualMachineHandler import VirtualMachineHandler

from thrift.transport import TSSLSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
import yaml
import click

USERNAME = 'OS_USERNAME'
PASSWORD = 'OS_PASSWORD'
PROJECT_NAME = 'OS_PROJECT_NAME'
PROJECT_ID = 'OS_PROJECT_ID'
USER_DOMAIN_ID = 'OS_USER_DOMAIN_NAME'
AUTH_URL = 'OS_AUTH_URL'

environment_variables = [
    USERNAME,
    PASSWORD,
    PROJECT_NAME,
    PROJECT_ID,
    USER_DOMAIN_ID,
    AUTH_URL,
]


@click.command()
@click.argument('config')
def startServer(config):
    click.echo("Start Cloud-Client-Portal Server")

    CONFIG_FILE = config

    with open(CONFIG_FILE, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
        HOST = cfg['openstack_connection']['host']
        PORT = cfg['openstack_connection']['port']
        CERTFILE = cfg['openstack_connection']['certfile']
    handler = VirtualMachineHandler(CONFIG_FILE)
    processor = Processor(handler)
    transport = TSSLSocket.TSSLServerSocket(
        host=HOST, port=PORT, certfile=CERTFILE)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    server = TServer.TThreadPoolServer(
        processor, transport, tfactory, pfactory)
    server.setNumThreads(15)
    server.serve()


def check_environment_variables(envs):
    def check_env(var):
        if var not in os.environ:
            click.echo("ERROR: There is no {} set in environment.".format(var))
            click.echo("Please make sure you have sourced your OpenStack rc file")
            sys.exit()

    list(map(lambda var: check_env(var), envs))


if __name__ == '__main__':
    check_environment_variables(environment_variables)
    startServer()
