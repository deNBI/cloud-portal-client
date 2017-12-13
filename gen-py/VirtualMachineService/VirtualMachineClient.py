import sys


from VirtualMachineService import Client
from ttypes import VM
import constants
from thrift import Thrift
from thrift.transport import TSSLSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol




def main():
    # Make socket
    transport = TSSLSocket.TSSLSocket('localhost', 9090)
    print('ping()')
    # Buffering is critical. Raw sockets are very slow
    transport = TTransport.TBufferedTransport(transport)

    # Wrap in a protocol
    protocol = TBinaryProtocol.TBinaryProtocol(transport)

    # Create a client to use the protocol encoder
    client = Client(protocol)

    # Connect!
    transport.open()






   # flav=vars(client.get_Flavors()[3])
    #img=vars(client.get_Images()[3])
   # print(flav)
    #print(client.get_Flavors())
   # print(client.create_keypair("test3"))
   # print(img)
   # print(client.get_server('Webapp2'))
    #keys={'username'}
    #metadata={"username":"dweere"}
    #print("----------------------------")
    #print(client.start_server(flavor=flav['name'], image=img['name'],keyname='neu',servername='thrif',metadata=metadata))
    print(client.get_servers())
    #print(client.add_floating_ip_to_server(servername='qwe4',network='cebitec'))
    #print(client.add_metadata_to_server(servername='thrift',metadata=metadata))
   # print(client.delete_metadata_from_server( servername='thrifttest',keys=keys))

main()