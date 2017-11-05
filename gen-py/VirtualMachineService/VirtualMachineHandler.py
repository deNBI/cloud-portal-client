from VirtualMachineService import Iface
from ttypes import VM,Flavor,Image
from openstack import connection
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

class VirtualMachineHandler(Iface):


    def create_connection(self, username, password, auth_url, project_name, user_domain_name, project_domain_name):
        conn = connection.Connection(username=USERNAME, password=PASSWORD, auth_url=AUTH_URL,
                                      project_name=PROJECT_NAME,
                                      user_domain_name=USER_DOMAIN_NAME, project_domain_name=PROJECT_DOMAIN_NAME)
        print(conn)
        return conn

    def __init__(self):
        self.conn =self.create_connection(username=USERNAME, password=PASSWORD, auth_url=AUTH_URL,
                                      project_name=PROJECT_NAME,
                                      user_domain_name=USER_DOMAIN_NAME, project_domain_name=PROJECT_DOMAIN_NAME)





    def get_Flavors(self):
            print (self.conn)
            flavors=list()
            for flav in self.conn.compute.flavors():
                flav=flav.to_dict()
                flavor=Flavor(vcpus=flav['vcpus'],ram=flav['ram'],disk=flav['disk'],name=flav['name'],openstack_id=flav['id'])
                flavors.append(flavor)
            return flavors
    def get_servers(self):

            servers=list()
            for serv in self.conn.compute.servers():
                serv=serv.to_dict()
                flav=self.conn.compute.get_flavor(serv['flavor']['id']).to_dict()
                print(flav)
                img=self.conn.compute.get_image(serv['image']['id']).to_dict()
                print(img)
                server=VM(flav=Flavor(vcpus=flav['vcpus'],ram=flav['ram'],disk=flav['disk'],name=flav['name'],openstack_id=flav['id']),
                          img=Image(name=img['name'],min_disk=img['min_disk'],min_ram=img['min_ram'],status=img['status'],created_at=img['created_at'],updated_at=img['updated_at'],openstack_id=img['id']),
                          status=serv['status'],metadata=serv['metadata'],project_id=serv['project_id'],keyname=serv['key_name'])
                servers.append(server)
            return servers

    def get_Images(self):

            images=list()
            for img in self.conn.compute.images():
                img=img.to_dict()
                image=Image(name=img['name'],min_disk=img['min_disk'],min_ram=img['min_ram'],status=img['status'],created_at=img['created_at'],updated_at=img['updated_at'],openstack_id=img['id'])
                images.append(image)
            return images
    def create_keypair(self, keyname):

        keypair = self.conn.compute.find_keypair(keyname)

        if not keypair:
            print("Create Key Pair:")
            keypair = self.conn.compute.create_keypair(name=keyname)
            print(keypair)

        return keypair

    def start_server(self, flavor, image, keyname, servername, network):


        image=self.conn.compute.find_image(image.name)
        flavor=self.conn.compute.find_flavor(flavor.name)
        network=self.conn.network.find_network(network)
        keypair=self.create_keypair(keyname)

        try:
            if self.conn.compute.find_server(servername) is not None:
                raise Exception

            server = self.conn.compute.create_server(
                name=servername, image_id=image.id, flavor_id=flavor.id,
                networks=[{"uuid": network.id}], key_name=keypair.name)

            # server = conn.compute.wait_for_server(server)

            return True
        except Exception as e:
            print("Create_Server_Error: " + e.__str__())
            return False

    def add_floating_ip_to_server(self,servername,network):
        server = self.conn.compute.find_server(servername)
        if server is None:
            return ('Server ' + servername + ' not found')
        server = self.conn.compute.get_server(server)
        print("Checking if Server already got an Floating IP")
        for values in server.addresses.values():
            for address in values:
                if address['OS-EXT-IPS:type'] == 'floating':
                    return ('Server ' + servername + ' already got an Floating IP ' + address['addr'])
        print("Checking if unused Floating IP exist")
        for floating_ip in self.conn.network.ips():
            if not floating_ip.fixed_ip_address:
                self.conn.compute.add_floating_ip_to_server(server, floating_ip.floating_ip_address)
                print("Adding existing Floating IP " + str(floating_ip.floating_ip_address) + "to  " + servername)
                return 'Added existing Floating IP ' + str(floating_ip.floating_ip_address) + " to Server " + servername
        print("Adding Floating IP to  " + servername)

        networkID = self.conn.network.find_network(network)
        floating_ip = self.conn.network.create_ip(floating_network_id=networkID)
        floating_ip = self.conn.network.get_ip(floating_ip)
        conn.compute.add_floating_ip_to_server(server, floating_ip.floating_ip_address)


        return 'Added new Floating IP' + floating_ip + " to Server" + servername

    def add_metadata_to_server(self,servername,metadata):
        server = self.conn.compute.find_server(servername)
        if server is None:
            return ('Server ' + servername + ' not found')
        server = self.conn.compute.get_server(server)
        self.conn.compute.set_server_metadata(server,**metadata)
        server = self.conn.compute.get_server(server)
        return server.metadata
    def delete_metadata_from_server(self,servername,keys):

        server = self.conn.compute.find_server(servername)
        if server is None:
            return ('Server ' + servername + ' not found')
        self.conn.compute.delete_server_metadata(server,keys)
        return keys