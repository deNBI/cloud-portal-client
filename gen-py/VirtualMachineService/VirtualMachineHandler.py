from VirtualMachineService import Iface
from ttypes import *
from constants import VERSION
from openstack import connection

from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client

import requests

import urllib
import os
import time
import datetime
import logging

import yaml


class VirtualMachineHandler(Iface):
    def create_connection(self):
        try:

            conn = connection.Connection(username=self.USERNAME, password=self.PASSWORD, auth_url=self.AUTH_URL,
                                         project_name=self.PROJECT_NAME,
                                         user_domain_name=self.USER_DOMAIN_NAME, project_domain_name='default')
            conn.authorize()
        except Exception as e:
            self.logger.error('Client failed authentication at Openstack')
            raise authenticationException(Reason='Client failed authentication at Openstack')

        self.logger.info("Connected to Openstack")
        return conn

    def __init__(self):
        # create logger with 'spam_application'
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        self.fh = logging.FileHandler('debug.log')
        self.fh.setLevel(logging.DEBUG)
        # create console handler with a higher log level
        self.ch = logging.StreamHandler()
        self.ch.setLevel(logging.INFO)
        # create formatter and add it to the handlers
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.fh.setFormatter(self.formatter)
        self.ch.setFormatter(self.formatter)
        # add the handlers to the logger
        self.logger.addHandler(self.fh)
        self.logger.addHandler(self.ch)
        self.USERNAME = os.environ['OS_USERNAME']
        self.PASSWORD = os.environ['OS_PASSWORD']
        self.PROJECT_NAME = os.environ['OS_PROJECT_NAME']
        self.PROJECT_ID = os.environ['OS_PROJECT_ID']
        self.USER_DOMAIN_NAME = os.environ['OS_USER_DOMAIN_NAME']
        self.AUTH_URL = os.environ['OS_AUTH_URL']

        with open("../../config.yml", 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
            self.USE_JUMPHOST = cfg['openstack_connection']['use_jumphost']
            self.NETWORK = cfg['openstack_connection']['network']
            self.FLOATING_IP_NETWORK = cfg['openstack_connection']['floating_ip_network']
            self.SET_PASSWORD = cfg['openstack_connection']['set_password']
            self.TAG = cfg['openstack_connection']['tag']
            if 'True' == str(self.USE_JUMPHOST):
                self.JUMPHOST_BASE = cfg['openstack_connection']['jumphost_base']
                self.JUMPHOST_IP = cfg['openstack_connection']['jumphost_ip']

        self.conn = self.create_connection()

    def setUserPassword(self, user, password):
        if str(self.SET_PASSWORD) == 'True':
            try:
                auth = v3.Password(auth_url=self.AUTH_URL, username=self.USERNAME, password=self.PASSWORD,
                                   project_name=self.PROJECT_NAME, user_domain_id='default',
                                   project_domain_id='default')
                sess = session.Session(auth=auth)

                def findUser(keystone, name):
                    users = keystone.users.list()
                    for user in users:
                        if user.__dict__['name'] == name:
                            return user

                keystone = client.Client(session=sess)
                user = findUser(keystone, user)
                keystone.users.update(user, password=password)
                return password
            except Exception as e:
                self.logger.error("Set Password for user {0} failed : {1}".format(user, str(e)))
                return otherException(Reason=str(e))
        else:
            raise otherException(Reason='Not allowed')

    def get_Flavors(self):
        self.logger.info("Get Flavors")
        flavors = list()
        for flav in filter(lambda x: self.TAG in x['extra_specs'] and x['extra_specs'][self.TAG] == 'True',
                           (list(self.conn.list_flavors(get_extra=True)))):
            flavor = Flavor(vcpus=flav['vcpus'], ram=flav['ram'], disk=flav['disk'], name=flav['name'],
                            openstack_id=flav['id'])
            flavors.append(flavor)
        return flavors

    def check_Version(self, version):
        self.logger.info("Compare Version : Server Version = " + str(VERSION) + " || Client Version = " + str(version))
        if version == VERSION:
            return True
        else:
            return False

    def get_Images(self):
        self.logger.info("Get Images")
        images = list()

        for img in filter(lambda x: 'tags' in x and self.TAG in x['tags'], self.conn.list_images()):
            metadata = img['metadata']

            if 'description' in metadata and 'default_user' in metadata:
                image = Image(name=img['name'], min_disk=img['min_disk'], min_ram=img['min_ram'],
                              status=img['status'], created_at=img['created_at'], updated_at=img['updated_at'],
                              openstack_id=img['id'], description=metadata['description'],
                              default_user=metadata['default_user'])


            elif 'description' in metadata:
                self.logger.warning("No default_user for " + img['name'])
                image = Image(name=img['name'], min_disk=img['min_disk'], min_ram=img['min_ram'],
                              status=img['status'], created_at=img['created_at'], updated_at=img['updated_at'],
                              openstack_id=img['id'], description=metadata['description'],
                              )
            elif 'default_user' in metadata:
                self.logger.warning("No Description for " + img['name'])
                image = Image(name=img['name'], min_disk=img['min_disk'], min_ram=img['min_ram'],
                              status=img['status'], created_at=img['created_at'], updated_at=img['updated_at'],
                              openstack_id=img['id'],
                              default_user=metadata['default_user'])
            else:
                self.logger.warning("No Description and default_user for " + img['name'])
                image = Image(name=img['name'], min_disk=img['min_disk'], min_ram=img['min_ram'],
                              status=img['status'], created_at=img['created_at'], updated_at=img['updated_at'],
                              openstack_id=img['id'],
                              )
            images.append(image)
        return images

    def import_keypair(self, keyname, public_key):
        keypair = self.conn.compute.find_keypair(keyname)
        if not keypair:
            self.logger.info("Create Keypair")

            keypair = self.conn.compute.create_keypair(name=keyname, public_key=public_key)
            return keypair
        elif keypair.public_key != public_key:
            self.logger.info("Key has changed. Replace old Key")
            self.conn.compute.delete_keypair(keypair)
            keypair = self.conn.compute.create_keypair(name=keyname, public_key=public_key)
            return keypair
        return keypair

    def get_server(self, servername):
        floating_ip = None
        fixed_ip = None
        self.logger.info("Get Server " + servername)

        server = self.conn.compute.find_server(servername)
        if server is None:
            self.logger.error("No Server with name " + servername)
            raise serverNotFoundException(Reason='No Server with name ' + servername)
        server = self.conn.compute.get_server(server)
        serv = server.to_dict()

        if serv['attached_volumes']:
            volume_id = serv['attached_volumes'][0]['id']
            diskspace = self.conn.block_storage.get_volume(volume_id).to_dict()['size']
        else:

            diskspace = 0
        if serv['launched_at']:
            dt = datetime.datetime.strptime(serv['launched_at'][:-7], '%Y-%m-%dT%H:%M:%S')
            timestamp = time.mktime(dt.timetuple())
        else:
            timestamp = None

        flav = self.conn.compute.get_flavor(serv['flavor']['id']).to_dict()
        img = self.conn.compute.get_image(serv['image']['id']).to_dict()
        default_user = 'default'
        try:
            default_user = img['metadata']['default_user']
        except Exception:
            pass
        for values in server.addresses.values():
            for address in values:

                if address['OS-EXT-IPS:type'] == 'floating':
                    floating_ip = address['addr']
                elif address['OS-EXT-IPS:type'] == 'fixed':
                    fixed_ip = address['addr']

        if floating_ip:
            server = VM(flav=Flavor(vcpus=flav['vcpus'], ram=flav['ram'], disk=flav['disk'], name=flav['name'],
                                    openstack_id=flav['id']),
                        img=Image(name=img['name'], min_disk=img['min_disk'], min_ram=img['min_ram'],
                                  status=img['status'],
                                  created_at=img['created_at'], updated_at=img['updated_at'], openstack_id=img['id'],
                                  default_user=default_user),
                        status=serv['status'], metadata=serv['metadata'], project_id=serv['project_id'],
                        keyname=serv['key_name'], openstack_id=serv['id'], name=serv['name'], created_at=str(timestamp),
                        floating_ip=floating_ip, fixed_ip=fixed_ip, diskspace=diskspace)
        else:
            server = VM(flav=Flavor(vcpus=flav['vcpus'], ram=flav['ram'], disk=flav['disk'], name=flav['name'],
                                    openstack_id=flav['id']),
                        img=Image(name=img['name'], min_disk=img['min_disk'], min_ram=img['min_ram'],
                                  status=img['status'], default_user=default_user,
                                  created_at=img['created_at'], updated_at=img['updated_at'], openstack_id=img['id']),
                        status=serv['status'], metadata=serv['metadata'], project_id=serv['project_id'],
                        keyname=serv['key_name'], openstack_id=serv['id'], name=serv['name'], created_at=str(timestamp),
                        fixed_ip=fixed_ip, diskspace=diskspace)
        return server


    def start_server(self, flavor, image, public_key, servername, elixir_id, diskspace):

        self.logger.info("Start Server {0}".format(servername))
        try:
            metadata = {'elixir_id': elixir_id}
            image = self.conn.compute.find_image(image)
            if image is None:
                self.logger.error('Image {0} not found!'.format(image))
                raise imageNotFoundException(Reason=('Image {0} not fournd'.format(image)))
            flavor = self.conn.compute.find_flavor(flavor)
            if flavor is None:
                self.logger.error('Flavor {0} not found!'.format(flavor))
                raise flavorNotFoundException(Reason='Flavor {0} not found!'.format(flavor))
            network = self.conn.network.find_network(self.NETWORK)
            if network is None:
                self.logger.error('Network {0} not found!'.format(network))
                raise networkNotFoundException(Reason='Network {0} not found!'.format(network))

            if self.conn.compute.find_server(servername) is not None:
                self.logger.error('Instance with name {0} already exist'.format(servername))
                raise nameException(Reason='Another Instance with name : {0} already exist'.format(servername))
            keyname = elixir_id[:-18]
            public_key = urllib.parse.unquote(public_key)
            keypair = self.import_keypair(keyname, public_key)
            server = self.conn.compute.create_server(
                name=servername, image_id=image.id, flavor_id=flavor.id,
                networks=[{"uuid": network.id}], key_name=keypair.name, metadata=metadata)

            return server.to_dict()['id']
        except Exception as e:
            self.logger.error(e)
            raise ressourceException(Reason=str(e))

    def attach_volume_to_server(self, openstack_id, diskspace):
        def checkStatusVolume(volume, conn):
            done = False
            while done == False:
                status = conn.block_storage.get_volume(volume).to_dict()['status']

                if status != 'available':

                    time.sleep(5)
                else:
                    done = True
                    time.sleep(10)
            return

        server = self.conn.compute.get_server(openstack_id)
        if server is None:
            self.logger.error("No Server with name {0} ".format(servername))
            raise serverNotFoundException(Reason='No Server with name {0}'.format(servername))
        serv = server.to_dict()
        servername = serv['name']
        self.logger.info('Creating volume with {0} GB diskspace'.format(diskspace))
        try:
            volume = self.conn.block_storage.create_volume(name=servername, size=int(diskspace)).to_dict()
        except Exception as e:
            self.logger.error(
                'Trying to create volume with {0} GB for vm {1} error : {2}'.format(diskspace, openstack_id, e),
                exc_info=True)
            return False
        checkStatusVolume(volume=volume['id'], conn=self.conn)
        self.logger.info('Attaching volume {0} to virtualmachine {1}'.format(volume['id'], openstack_id))
        try:
            self.conn.compute.create_volume_attachment(server=server, volumeId=volume['id'])
        except Exception as e:
            self.logger.error(
                'Trying to attache volume {0} to vm {1} error : {2}'.format(volume['id'], openstack_id, e),
                exc_info=True)
            self.logger.info("Delete Volume  {0}".format(volume_id))
            conn.block_storage.delete_volume(volume=volume_id)
            return False

        return True




    def check_server_status(self, openstack_id,diskspace):
        self.logger.info('Check Status VM {0}'.format(openstack_id))
        try:
            server = self.conn.compute.get_server(openstack_id)
        except Exception:
            self.logger.error("No Server with id  {0} ".format(openstack_id))
            return None
        if server is None:
            self.logger.error("No Server with id {0} ".format(openstack_id))
            return None
        serv = server.to_dict()
        servername = serv['name']

        if serv['status'] == 'ACTIVE':
            if diskspace > 0:
                attached=self.attach_volume_to_server(openstack_id=openstack_id, diskspace=diskspace)

                if attached is False:
                    server=self.get_server(servername)
                    self.delete_server(openstack_id=openstack_id)
                    server.status='DESTROYED'
                    return server
                return self.get_server(servername)
            return self.get_server(servername)
        else:
            server=self.get_server(servername)
            server.status='BUILD'
            return server






    def generate_SSH_Login_String(self,servername):
        #check if jumphost is active

        if 'True' == str(self.USE_JUMPHOST):
            server = self.get_server(servername=servername)
            img = server.img
            default_user = img.default_user
            server_base = server.fixed_ip.split(".")[-1]
            port = int(self.JUMPHOST_BASE) + int(server_base) * 3
            ssh_command = "ssh -i private_key_file " + str(default_user) + "@" + str(self.JUMPHOST_IP) + " -p " + str(
                port)

            return ssh_command

        else:
            floating_ip = self.add_floating_ip_to_server(servername, self.FLOATING_IP_NETWORK)
            server = self.get_server(servername=servername)
            img = server.img

            default_user = img.default_user

            return "ssh -i private_key_file " + str(default_user) + "@" + str(floating_ip)

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
                self.logger.info(
                    "Adding existing Floating IP " + str(floating_ip.floating_ip_address) + "to  " + servername)
                return str(floating_ip.floating_ip_address)

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
        self.logger.info("Delete Server " + openstack_id)
        server = self.conn.compute.get_server(openstack_id)
        if server is None:
            self.logger.error("Instance {0} not found".format(openstack_id))
            raise serverNotFoundException

        if server.status == 'SUSPENDED':
            self.conn.compute.resume_server(server)
            server = self.conn.compute.get_server(server)
            while server.status != 'ACTIVE':
                server = self.conn.compute.get_server(server)
                time.sleep(3)


        attachments = list()
        volumeids = list()

        for volume in self.conn.compute.volume_attachments(server=server):
            attachments.append(volume)
            volumeids.append(volume.to_dict()['volume_id'])


        def deleteVolumeAttachmenServer(attachments,server,logger,conn):

            for a in attachments:
                logger.info("Delete VolumeAttachment  {0}".format(a))
                conn.compute.delete_volume_attachment(volume_attachment=a, server=server)

        deleteVolumeAttachmenServer(attachments=attachments, server=server, logger=self.logger, conn=self.conn)

        def checkStatusVolumes(volumes, conn):
            done = False
            while done == False:
                done = True
                for a in volumes:
                    if conn.block_storage.get_volume(a).to_dict()['status'] != 'available':
                        conn.block_storage.get_volume(a).to_dict()['status']
                        done = False
                        time.sleep(5)
                        break
            return

        checkStatusVolumes(volumeids, self.conn)

        def deleteVolume(volume_id, conn, logger):
            logger.info("Delete Volume  {0}".format(volume_id))
            conn.block_storage.delete_volume(volume=volume_id)

        for id in volumeids:
            deleteVolume(id, self.conn, self.logger)
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
            server = self.conn.compute.get_server(server)
            while server.status != 'SUSPENDED':
                server = self.conn.compute.get_server(server)
                time.sleep(3)

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
            while server.status != 'ACTIVE':
                server = self.conn.compute.get_server(server)
                time.sleep(3)

            return True
        else:

            return False
