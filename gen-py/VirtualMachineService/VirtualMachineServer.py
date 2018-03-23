

from VirtualMachineService import Client,Processor
from VirtualMachineHandler import VirtualMachineHandler
from thrift.transport import TSSLSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
import yaml



if __name__ == '__main__':
    with open("../../config.yml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
        HOST = cfg['openstack_connection']['host']
        PORT = cfg['openstack_connection']['port']
        CERTFILE = cfg['openstack_connection']['certfile']
    handler=VirtualMachineHandler()
    processor=Processor(handler)
    transport = TSSLSocket.TSSLServerSocket(host=HOST, port=PORT,certfile=CERTFILE)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
    server.serve()


