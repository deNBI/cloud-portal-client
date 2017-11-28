from VirtualMachineService import Iface
from ttypes import *
from openstack import connection
import config
import urllib
import os
import time
import datetime


NETWORK=config.network
USERNAME=config.username
PASSWORD=config.password
AUTH_URL=config.auth_url
PROJECT_NAME=config.project_name
USER_DOMAIN_NAME=config.user_domain_name
PROJECT_DOMAIN_NAME=config.project_domain_name
FLAVOR_FILTER=config.flavor_filter

class VirtualMachineHandler(Iface):


    def create_connection(self, username, password, auth_url, project_name, user_domain_name, project_domain_name):
        try:
            conn = connection.Connection(username=USERNAME, password=PASSWORD, auth_url=AUTH_URL,
                                          project_name=PROJECT_NAME,
                                          user_domain_name=USER_DOMAIN_NAME, project_domain_name=PROJECT_DOMAIN_NAME)
        except Exception:
            raise authenticationException

        print(conn)
        return conn

    def __init__(self):
        self.conn =self.create_connection(username=USERNAME, password=PASSWORD, auth_url=AUTH_URL,
                                      project_name=PROJECT_NAME,
                                      user_domain_name=USER_DOMAIN_NAME, project_domain_name=PROJECT_DOMAIN_NAME)




    def get_Flavors(self):
            print("Get Flavors")
            flavors=list()
            for flav in self.conn.compute.flavors():

                flav=flav.to_dict()
                flav.pop('links',None)


                if any(x in flav['name'] for x in FLAVOR_FILTER):

                    print(flav)
                    flavor=Flavor(vcpus=flav['vcpus'],ram=flav['ram'],disk=flav['disk'],name=flav['name'],openstack_id=flav['id'])
                    flavors.append(flavor)
            return flavors
    def get_servers(self):
            print("Get Servers")
            servers=list()
            for serv in self.conn.compute.servers():
                serv=serv.to_dict()
                print(serv)
                flav=self.conn.compute.get_flavor(serv['flavor']['id']).to_dict()
                img=self.conn.compute.get_image(serv['image']['id']).to_dict()
                server=VM(flav=Flavor(vcpus=flav['vcpus'],ram=flav['ram'],disk=flav['disk'],name=flav['name'],openstack_id=flav['id']),
                          img=Image(name=img['name'],min_disk=img['min_disk'],min_ram=img['min_ram'],status=img['status'],created_at=img['created_at'],updated_at=img['updated_at'],openstack_id=img['id']),
                          status=serv['status'],metadata=serv['metadata'],project_id=serv['project_id'],keyname=serv['key_name'],openstack_id=serv['id'],name=serv['name'])
                servers.append(server)
            return servers

    def get_Images(self):
            print("Get Images")
            images=list()
            print(self.conn.compute.images())
            for img in self.conn.compute.images():
                print('inside')
                img=img.to_dict()
                img.pop('links',None)
                print(img)

                try:
                    image = Image(name=img['name'], min_disk=img['min_disk'], min_ram=img['min_ram'],
                                  status=img['status'], created_at=img['created_at'], updated_at=img['updated_at'],
                                  openstack_id=img['id'],description=img['metadata']['description'])

                    print(image)
                except KeyError :
                    image = Image(name=img['name'], min_disk=img['min_disk'], min_ram=img['min_ram'],
                                  status=img['status'], created_at=img['created_at'], updated_at=img['updated_at'],
                                  openstack_id=img['id'])

                images.append(image)
            #print(images)
            print("Done Images")
            return images
    def import_keypair(self,keyname,public_key):
        keypair = self.conn.compute.find_keypair(keyname)
        if not keypair:
            print("Create Key Pair")
            print("Keyname " + keyname)
            print("Key " + public_key)
            keypair=self.conn.compute.create_keypair(name=keyname,public_key=public_key)
            return keypair
        return keypair
    def create_keypair(self, keyname):
        print("Create Keypair")
        SSH_DIR= '{home}/.ssh'.format(home=os.path.expanduser("~"))
        PRIVATE_KEYPAIR='{ssh_dir}/id_rsa.{key}'.format(
            ssh_dir=SSH_DIR, key=keyname)
        keypair = self.conn.compute.find_keypair(keyname)

        if not keypair:
            print("Create Key Pair:")
            keypair = self.conn.compute.create_keypair(name=keyname)
            print(keypair)




        return keypair
    def get_server(self,servername):
        print("Get Server " + servername)

        server=self.conn.compute.find_server(servername)
        if server is None:
            raise serverNotFoundException
        server=self.conn.compute.get_server(server)
        serv = server.to_dict()
        dt = datetime.datetime.strptime(serv['launched_at'][:-7], '%Y-%m-%dT%H:%M:%S')
        timestamp = time.mktime(dt.timetuple())

        print(timestamp)
        print(datetime.datetime.fromtimestamp(timestamp).isoformat())
        print(serv)
        flav = self.conn.compute.get_flavor(serv['flavor']['id']).to_dict()
        img = self.conn.compute.get_image(serv['image']['id']).to_dict()
        server = VM(flav=Flavor(vcpus=flav['vcpus'], ram=flav['ram'], disk=flav['disk'], name=flav['name'],
                                openstack_id=flav['id']),
                    img=Image(name=img['name'], min_disk=img['min_disk'], min_ram=img['min_ram'], status=img['status'],
                              created_at=img['created_at'], updated_at=img['updated_at'], openstack_id=img['id']),
                    status=serv['status'], metadata=serv['metadata'], project_id=serv['project_id'],
                    keyname=serv['key_name'], openstack_id=serv['id'], name=serv['name'],created_at=str(timestamp))
        return server
    def start_server(self, flavor, image,public_key, servername,username,elixir_id):
        print("Start Server "+ servername)
        try:
            metadata={'username':username,'elixir_id':elixir_id}
            image=self.conn.compute.find_image(image)
            if image is None:
                raise imageNotFoundException
            flavor=self.conn.compute.find_flavor(flavor)
            if flavor is None:
                raise flavorNotFoundException
            network=self.conn.network.find_network(NETWORK)
            if network is None:
                print("Network not found")
                raise networkNotFoundException



            if self.conn.compute.find_server(servername) is not None:
                    print(self.conn.compute.find_server(servername))
                    raise nameException
            keyname=elixir_id[:-18]
            public_key=urllib.parse.unquote(public_key)
            keypair = self.import_keypair(keyname,public_key)
            server = self.conn.compute.create_server(
                    name=servername, image_id=image.id, flavor_id=flavor.id,
                    networks=[{"uuid": network.id}], key_name=keypair.name,metadata=metadata)

            server = self.conn.compute.wait_for_server(server)
            return True
        except Exception as e:
            raise nameException(Reason=str(e))





    def add_floating_ip_to_server(self,servername,network):
        server = self.conn.compute.find_server(servername)
        if server is None:
            raise serverNotFoundException
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
        if networkID is None:
            raise networkNotFoundException
        floating_ip = self.conn.network.create_ip(floating_network_id=networkID)
        floating_ip = self.conn.network.get_ip(floating_ip)
        self.conn.compute.add_floating_ip_to_server(server, floating_ip.floating_ip_address)


        return 'Added new Floating IP' + floating_ip + " to Server" + servername

    def add_metadata_to_server(self,servername,metadata):
        server = self.conn.compute.find_server(servername)
        if server is None:
            raise serverNotFoundException
        server = self.conn.compute.get_server(server)
        self.conn.compute.set_server_metadata(server,**metadata)
        server = self.conn.compute.get_server(server)
        return server.metadata

    def delete_metadata_from_server(self,servername,keys):

        server = self.conn.compute.find_server(servername)
        if server is None:
            raise serverNotFoundException
        self.conn.compute.delete_server_metadata(server,keys)
        return keys


    def stop_server(self,openstack_id):


        server = self.conn.compute.get_server(openstack_id)
        if server is None:
            raise serverNotFoundException
        print(server.status)

        if server.status == 'ACTIVE':
            self.conn.compute.stop_server(server)

            return "Stopped Server "
        else:

            return 'Server ' + servername + ' was already stopped'

    def pause_server(self, servername):

        server = self.conn.compute.find_server(servername)
        if server is None:
            raise serverNotFoundException
        server = self.conn.compute.get_server(server)
        status = server.status
        if status == 'ACTIVE':
            self.conn.compute.pause_server(server)
            return 'server:' + servername + ' status:"PAUSED"'

        elif status == 'PAUSED':
            return 'server:' + servername + ' status:"PAUSED"'
        else:
            return 'server:' + servername + ' status:"TODO"'

    def unpause_server(self,servername):

        server = self.conn.compute.find_server(servername)
        if server is None:
            return 'server:' + servername + ' status:"NOTFOUND"'
        server = conn.compute.get_server(server)
        status = server.status
        if status == 'ACTIVE':
            return 'server:' + servername + ' status:"ACTIVE"'
        elif status == 'PAUSED':
            self.conn.compute.unpause_server(server)
            return 'server:' + servername + ' status:"ACTIVE"'
        else:
            return 'server:' + servername + ' status:"TODO"'

