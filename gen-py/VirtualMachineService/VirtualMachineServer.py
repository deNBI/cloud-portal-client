

from VirtualMachineService import Client,Processor
from VirtualMachineHandler import VirtualMachineHandler
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
import config
HOST=config.server_host
PORT=config.server_port


if __name__ == '__main__':
    handler=VirtualMachineHandler()
    processor=Processor(handler)
    transport = TSocket.TServerSocket(host=HOST, port=PORT)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
    server.serve()

