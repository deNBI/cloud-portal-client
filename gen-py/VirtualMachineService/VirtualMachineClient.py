import sys


from VirtualMachineService import Client
from ttypes import VM
import constants
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
import configparser

config=configparser.ConfigParser()
config.read('config.cfg')
NETWORK=config.get('Connection','network')
USERNAME=config.get('Connection','username')
PASSWORD=config.get('Connection','password')
AUTH_URL=config.get('Connection','auth_url')
PROJECT_NAME=config.get('Connection','project_name')
USER_DOMAIN_NAME=config.get('Connection','user_domain_name')
PROJECT_DOMAIN_NAME=config.get('Connection','project_domain_name')

def main():
    # Make socket
    transport = TSocket.TSocket('localhost', 9090)
    print('ping()')
    # Buffering is critical. Raw sockets are very slow
    transport = TTransport.TBufferedTransport(transport)

    # Wrap in a protocol
    protocol = TBinaryProtocol.TBinaryProtocol(transport)

    # Create a client to use the protocol encoder
    client = Client(protocol)

    # Connect!
    transport.open()
    flavors=constants.FLAVOR_LIST
    images=constants.IMAGES_LIST

    flavors = flavors[1]
    images = images[1]


    print(client.start_server(username=USERNAME,password=PASSWORD,auth_url=AUTH_URL,project_name=PROJECT_NAME,user_domain_name=USER_DOMAIN_NAME,project_domain_name=PROJECT_DOMAIN_NAME,flavor=flavors, image=images,keyname='neutest',servername='thrifttest',network=NETWORK))

main()