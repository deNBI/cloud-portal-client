

from VirtualMachineService import Client,Processor
from VirtualMachineHandler import VirtualMachineHandler
from thrift.transport import TSSLSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
import config
import ssl
HOST=config.server_host
PORT=config.server_port
CERTFILE=config.server_cert


if __name__ == '__main__':
    handler=VirtualMachineHandler()
    processor=Processor(handler)
    transport = TSSLSocket.TSSLServerSocket(host=HOST, port=PORT,cert_reqs=ssl.CERT_REQUIRED,certfile=CERTFILE,keyfile='test/keys/server.p12',)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
    server.serve()

