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






    flav=client.get_Flavors()[1]
    img=client.get_Images()[1]
    print(flav)
    print(img)
    keys={'username'}
    metadata={"username":"dweere"}
    #print(client.start_server(flavor=flav, image=img,keyname='neu',servername='thrift',network='portalnetzwerk'))
    print(client.get_servers())
    print(client.add_floating_ip_to_server(servername='thrift',network='cebitec'))
    print(client.add_metadata_to_server(servername='thrift',metadata=metadata))
   # print(client.delete_metadata_from_server( servername='thrifttest',keys=keys))

main()