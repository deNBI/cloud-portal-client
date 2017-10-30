import sys


from VirtualMachineService import Client
from ttypes import VM
import constants
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol


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

    vm=VM(flavors[1],images[1])
    print(client.start_server(vm,'neutest','thrifttest'))

main()