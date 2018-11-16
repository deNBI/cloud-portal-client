import os
import sys

try:
    from VirtualMachineService import Client, Processor
    from VirtualMachineHandler import VirtualMachineHandler
except Exception as e:
    from .VirtualMachineService import Client, Processor
    from .VirtualMachineHandler import VirtualMachineHandler

from thrift.transport import TSSLSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
import yaml
import click

DEFAULT_CONFIG = 'config/config.yml'
@click.command()
@click.option('--config', default=DEFAULT_CONFIG,help= 'path to the config file')
def startServer(config):
    click.echo("Start Cloud-Client-Portal Server")
    if config == DEFAULT_CONFIG:
        CONFIG_FILE = os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)),
            config)
    else:
        CONFIG_FILE=config

    with open(CONFIG_FILE, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
        HOST = cfg['openstack_connection']['host']
        PORT = cfg['openstack_connection']['port']
        CERTFILE = cfg['openstack_connection']['certfile']
    handler = VirtualMachineHandler()
    processor = Processor(handler)
    transport = TSSLSocket.TSSLServerSocket(
        host=HOST, port=PORT, certfile=CERTFILE)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    server = TServer.TThreadPoolServer(
        processor, transport, tfactory, pfactory)
    server.setNumThreads(15)
    server.serve()


if __name__ == '__main__':
    startServer()
