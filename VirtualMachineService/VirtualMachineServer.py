from VirtualMachineService import Client, Processor
from VirtualMachineHandler import VirtualMachineHandler
from thrift.transport import TSSLSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
import yaml, os

if __name__ == '__main__':
    CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'config.yml')

    with open(CONFIG_FILE, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
        HOST = cfg['openstack_connection']['host']
        PORT = cfg['openstack_connection']['port']
        CERTFILE = cfg['openstack_connection']['certfile']
    handler = VirtualMachineHandler()
    processor = Processor(handler)
    transport = TSSLSocket.TSSLServerSocket(host=HOST, port=PORT, certfile=CERTFILE)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
    server.setNumThreads(15)
    server.serve()
