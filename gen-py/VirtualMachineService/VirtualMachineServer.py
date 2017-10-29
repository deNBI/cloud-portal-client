
import configparser
from VirtualMachineService import Client,Processor
from VirtualMachineHandler import VirtualMachineHandler
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

config=configparser.ConfigParser()
config.read('config.cfg')
NETWORK=config.get('Connection','network')
USERNAME=config.get('Connection','username')
PASSWORD=config.get('Connection','password')
AUTH_URL=config.get('Connection','auth_url')
PROJECT_NAME=config.get('Connection','project_name')
USER_DOMAIN_NAME=config.get('Connection','user_domain_name')
PROJECT_DOMAIN_NAME=config.get('Connection','project_domain_name')


if __name__ == '__main__':
    handler=VirtualMachineHandler(username=USERNAME,password=PASSWORD,network=NETWORK,auth_url=AUTH_URL,project_name=PROJECT_NAME,user_domain_name=USER_DOMAIN_NAME,project_domain_name=PROJECT_DOMAIN_NAME)
    processor=Processor(handler)
    transport = TSocket.TServerSocket(port=9090)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
    server.serve()

