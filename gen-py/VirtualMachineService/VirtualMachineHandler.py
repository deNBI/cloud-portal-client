from VirtualMachineService import Iface
from ttypes import *
from constants import VERSION
from openstack import connection
import config
import urllib
import os
import time
import datetime
import logging

NETWORK = config.network
USERNAME = config.username
PASSWORD = config.password
AUTH_URL = config.auth_url
PROJECT_NAME = config.project_name
USER_DOMAIN_NAME = config.user_domain_name
PROJECT_DOMAIN_NAME = config.project_domain_name
FLAVOR_FILTER = config.flavor_filter
FLOATING_IP_NETWORK='cebitec'


class VirtualMachineHandler(Iface):
    def create_connection(self, username, password, auth_url, project_name, user_domain_name, project_domain_name):
        try:
            conn = connection.Connection(username=USERNAME, password=PASSWORD, auth_url=AUTH_URL,
                                         project_name=PROJECT_NAME,
                                         user_domain_name=USER_DOMAIN_NAME, project_domain_name=PROJECT_DOMAIN_NAME)
            conn.authorize()
        except Exception:
            self.logger.error('Client failed authentication at Openstack')
            raise authenticationException(Reason='Client failed authentication at Openstack')

        self.logger.info("Connected to Openstack")
        return conn

    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.conn = self.create_connection(username=USERNAME, password=PASSWORD, auth_url=AUTH_URL,
                                           project_name=PROJECT_NAME,
                                           user_domain_name=USER_DOMAIN_NAME, project_domain_name=PROJECT_DOMAIN_NAME)


    def get_Flavors(self):
        self.logger.info("Get Flavors")
        flavors = list()
        for flav in self.conn.compute.flavors():

            flav = flav.to_dict()
            flav.pop('links', None)

            if any(x in flav['name'] for x in FLAVOR_FILTER):

                flavor = Flavor(vcpus=flav['vcpus'], ram=flav['ram'], disk=flav['disk'], name=flav['name'],
                                openstack_id=flav['id'])
                flavors.append(flavor)
        return flavors


    def check_Version(self, version):
        self.logger.info("Compare Version : Server Version = " + str(VERSION) +" || Client Version = " + str(version))
        if version == VERSION:
            return True
        else:
            return False

    def get_Images(self):
        self.logger.info("Get Images")
        images = list()

        for img in self.conn.compute.images():

            img = img.to_dict()
            img.pop('links', None)


            try:
                image = Image(name=img['name'], min_disk=img['min_disk'], min_ram=img['min_ram'],
                              status=img['status'], created_at=img['created_at'], updated_at=img['updated_at'],
                              openstack_id=img['id'], description=img['metadata']['description'])


            except KeyError:
                self.logger.warning("No Description for " + img['name'])
                image = Image(name=img['name'], min_disk=img['min_disk'], min_ram=img['min_ram'],
                              status=img['status'], created_at=img['created_at'], updated_at=img['updated_at'],
                              openstack_id=img['id'])

            images.append(image)
        return images

    def import_keypair(self, keyname, public_key):
        keypair = self.conn.compute.find_keypair(keyname)
        if not keypair:
            self.logger.info("Create Keypair")


            keypair = self.conn.compute.create_keypair(name=keyname, public_key=public_key)
            return keypair
        elif keypair.public_key != public_key:
            self.logger.info("Key has changed.Replace old Key")
            self.conn.compute.delete_keypair(keypair)
            keypair = self.conn.compute.create_keypair(name=keyname, public_key=public_key)
            return keypair
        return keypair
    def get_server(self, servername):
        self.logger.info("Get Server " + servername)

        server = self.conn.compute.find_server(servername)
        if server is None:
            self.logger.error("No Server with name " + servername)
            raise serverNotFoundException(Reason='No Server with name ' + servername)
        server = self.conn.compute.get_server(server)
        serv = server.to_dict()

        dt = datetime.datetime.strptime(serv['launched_at'][:-7], '%Y-%m-%dT%H:%M:%S')
        timestamp = time.mktime(dt.timetuple())

        flav = self.conn.compute.get_flavor(serv['flavor']['id']).to_dict()
        img = self.conn.compute.get_image(serv['image']['id']).to_dict()
        for values in server.addresses.values():
            for address in values:
                if address['OS-EXT-IPS:type'] == 'floating':
                    floating_ip = address['addr']
        server = VM(flav=Flavor(vcpus=flav['vcpus'], ram=flav['ram'], disk=flav['disk'], name=flav['name'],
                                openstack_id=flav['id']),
                    img=Image(name=img['name'], min_disk=img['min_disk'], min_ram=img['min_ram'], status=img['status'],
                              created_at=img['created_at'], updated_at=img['updated_at'], openstack_id=img['id']),
                    status=serv['status'], metadata=serv['metadata'], project_id=serv['project_id'],
                    keyname=serv['key_name'], openstack_id=serv['id'], name=serv['name'], created_at=str(timestamp),
                    floating_ip=floating_ip)
        return server

    def start_server(self, flavor, image, public_key, servername, username, elixir_id):
        self.logger.info("Start Server" +  servername)
        try:
            metadata = {'username': username, 'elixir_id': elixir_id}
            image = self.conn.compute.find_image(image)
            if image is None:
                self.logger.error("Image " + image + " not found")
                raise imageNotFoundException(Reason='Image ' + image + ' was not found!')
            flavor = self.conn.compute.find_flavor(flavor)
            if flavor is None:
                self.logger.error("Flavor " + image + " not found")
                raise flavorNotFoundException(Reason='Flavor' + flavor + ' was not found!')
            network = self.conn.network.find_network(NETWORK)
            if network is None:
                self.logger.error("Network " + image + " not found")
                raise networkNotFoundException(Reason='Network ' + network + 'was not found!')

            if self.conn.compute.find_server(servername) is not None:
                self.logger.error("Instance with name " + servername + ' already exist')
                raise nameException(Reason='Another Instance with name : ' + servername + ' already exist')
            keyname = elixir_id[:-18]
            public_key = urllib.parse.unquote(public_key)
            keypair = self.import_keypair(keyname, public_key)
            server = self.conn.compute.create_server(
                name=servername, image_id=image.id, flavor_id=flavor.id,
                networks=[{"uuid": network.id}], key_name=keypair.name, metadata=metadata)

            server = self.conn.compute.wait_for_server(server)
            self.add_floating_ip_to_server(servername, FLOATING_IP_NETWORK)
            return True
        except Exception as e:
            if 'Quota exceeded ' in str(e):
                self.logger.error("Quoata exceeded : not enough Ressources left")
                raise ressourceException(Reason=str(e))

            raise otherException(Reason=str(e))

    def add_floating_ip_to_server(self, servername, network):
        server = self.conn.compute.find_server(servername)
        if server is None:
            self.logger.error("Instance " + servername + "not found")
            raise serverNotFoundException
        server = self.conn.compute.get_server(server)
        self.logger.info("Checking if Server already got an Floating Ip")
        for values in server.addresses.values():
            for address in values:
                if address['OS-EXT-IPS:type'] == 'floating':
                    return address['addr']
        self.logger.info("Checking if unused Floating-Ip exist")


        for floating_ip in self.conn.network.ips():
            if not floating_ip.fixed_ip_address:
                self.conn.compute.add_floating_ip_to_server(server, floating_ip.floating_ip_address)
                self.logger.info("Adding existing Floating IP " + str(floating_ip.floating_ip_address) + "to  " + servername)
                return 'Added existing Floating IP ' + str(floating_ip.floating_ip_address) + " to Server " + servername

        networkID = self.conn.network.find_network(network)
        if networkID is None:
            self.logger.error("Network " + network + " not found")
            raise networkNotFoundException
        networkID = networkID.to_dict()['id']
        floating_ip = self.conn.network.create_ip(floating_network_id=networkID)
        floating_ip = self.conn.network.get_ip(floating_ip)
        self.conn.compute.add_floating_ip_to_server(server, floating_ip.floating_ip_address)

        return floating_ip


    def delete_server(self, openstack_id):
        self.logger.info("Delete Server " + openstack_id )
        server = self.conn.compute.get_server(openstack_id)
        if server is None:
            self.logger.error("Instance " + openstack_id + " not found")
            raise serverNotFoundException
        self.conn.compute.delete_server(server)
        return True

    def stop_server(self, openstack_id):
        self.logger.info("Stop Server " + openstack_id)
        server = self.conn.compute.get_server(openstack_id)
        if server is None:
            self.logger.error("Instance " + openstack_id + " not found")
            raise serverNotFoundException


        if server.status == 'ACTIVE':
            self.conn.compute.suspend_server(server)

            return True
        else:

            return False


    def resume_server(self, openstack_id):
        self.logger.info("Resume Server " + openstack_id)
        server = self.conn.compute.get_server(openstack_id)
        if server is None:
            self.logger.error("Instance " + openstack_id + " not found")
            raise serverNotFoundException


        if server.status == 'SUSPENDED':
            self.conn.compute.resume_server(server)

            return True
        else:

            return False
