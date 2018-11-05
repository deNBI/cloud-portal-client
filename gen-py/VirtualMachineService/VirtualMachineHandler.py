from VirtualMachineService import Iface
from ttypes import *
from constants import VERSION
from openstack import connection

from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client
import socket
from contextlib import closing
import requests

import urllib
import os
import time
import datetime
import logging

import yaml

import base64
from oslo_utils import encodeutils


class VirtualMachineHandler(Iface):
    def create_connection(self):
        try:

            conn = connection.Connection(username=self.USERNAME, password=self.PASSWORD, auth_url=self.AUTH_URL,
                                         project_name=self.PROJECT_NAME,
                                         user_domain_name=self.USER_DOMAIN_NAME, project_domain_name='default')
            conn.authorize()
        except Exception as e:
            self.logger.error('Client failed authentication at Openstack : {0}', e)
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
        self.SSH_PORT = 22

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
        try:
            for flav in filter(lambda x: self.TAG in x['extra_specs'] and x['extra_specs'][self.TAG] == 'True',
                               (list(self.conn.list_flavors(get_extra=True)))):
                flavor = Flavor(vcpus=flav['vcpus'], ram=flav['ram'], disk=flav['disk'], name=flav['name'],
                                openstack_id=flav['id'])
                flavors.append(flavor)
            return flavors
        except Exception as e:
            self.logger.error("Get Flavors Error: {0}".format(e))
            return ()

    def check_Version(self, version):
        self.logger.info("Compare Version : Server Version = {0} || Client Version = {1}".format(VERSION, version))
        try:
            if version == VERSION:
                return True
            else:
                return False
        except Exception as e:
            self.logger.error("Compare Version Error: {0}".format(e))
            return False

    def get_client_version(self):
        self.logger.info("Get Version of Client: {}".format(VERSION))
        return str(VERSION)

    def get_Images(self):
        self.logger.info("Get Images")
        images = list()
        try:
            for img in filter(lambda x: 'tags' in x and len(x['tags']) > 0 and x['status'] == 'active',
                              self.conn.list_images()):

                metadata = img['metadata']
                description = metadata.get('description')
                tags = img.get('tags')
                if description is None:
                    self.logger.warning("No Description and  for " + img['name'])

                image = Image(name=img['name'], min_disk=img['min_disk'], min_ram=img['min_ram'],
                              status=img['status'], created_at=img['created_at'], updated_at=img['updated_at'],
                              openstack_id=img['id'], description=description, tag=tags
                              )
                images.append(image)

            return images
        except Exception as e:
            self.logger.error("Get Images Error: {0}".format(e))
            return ()

    def get_Image_with_Tag(self, id):
        self.logger.info("Get Image {0} with tags".format(id))
        try:
            images = self.conn.list_images()
            img = list(filter(lambda image: image['id'] == id, images))[0]
            metadata = img['metadata']
            description = metadata.get('description')
            tags = img.get('tags')
            image = Image(name=img['name'], min_disk=img['min_disk'], min_ram=img['min_ram'],
                          status=img['status'], created_at=img['created_at'], updated_at=img['updated_at'],
                          openstack_id=img['id'], description=description, tag=tags
                          )
            return image
        except Exception as e:
            self.logger.error("Get Image {0} with Tag Error: {1}".format(id, e))
            return

    def import_keypair(self, keyname, public_key):
        try:
            keypair = self.conn.compute.find_keypair(keyname)
            if not keypair:
                self.logger.info("Create Keypair {0}".format(keyname))

                keypair = self.conn.compute.create_keypair(name=keyname, public_key=public_key)
                return keypair
            elif keypair.public_key != public_key:
                self.logger.info("Key has changed. Replace old Key")
                self.conn.compute.delete_keypair(keypair)
                keypair = self.conn.compute.create_keypair(name=keyname, public_key=public_key)
                return keypair
            return keypair
        except Exception as e:
            self.logger.error('Import Keypair {0} error:{1}'.format(keyname, e))
            return

    def get_server(self, openstack_id):
        floating_ip = None
        fixed_ip = None
        self.logger.info("Get Server {0}".format(openstack_id))
        server = self.conn.compute.get_server(openstack_id)
        if server is None:
            self.logger.error("No Server  {0}".format(openstack_id))
            raise serverNotFoundException(Reason="No Server {0}".format(openstack_id))
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
        img = self.get_Image_with_Tag(serv['image']['id'])
        for values in server.addresses.values():
            for address in values:

                if address['OS-EXT-IPS:type'] == 'floating':
                    floating_ip = address['addr']
                elif address['OS-EXT-IPS:type'] == 'fixed':
                    fixed_ip = address['addr']

        if floating_ip:
            server = VM(flav=Flavor(vcpus=flav['vcpus'], ram=flav['ram'], disk=flav['disk'], name=flav['name'],
                                    openstack_id=flav['id']),
                        img=img,
                        status=serv['status'], metadata=serv['metadata'], project_id=serv['project_id'],
                        keyname=serv['key_name'], openstack_id=serv['id'], name=serv['name'], created_at=str(timestamp),
                        floating_ip=floating_ip, fixed_ip=fixed_ip, diskspace=diskspace)
        else:
            server = VM(flav=Flavor(vcpus=flav['vcpus'], ram=flav['ram'], disk=flav['disk'], name=flav['name'],
                                    openstack_id=flav['id']),
                        img=img,
                        status=serv['status'], metadata=serv['metadata'], project_id=serv['project_id'],
                        keyname=serv['key_name'], openstack_id=serv['id'], name=serv['name'], created_at=str(timestamp),
                        fixed_ip=fixed_ip, diskspace=diskspace)
        return server

    def start_server(self, flavor, image, public_key, servername, elixir_id, diskspace, volumename):
        print(flavor)

        volumeId = ''
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

            keyname = elixir_id[:-18]
            public_key = urllib.parse.unquote(public_key)
            keypair = self.import_keypair(keyname, public_key)

            if diskspace > '0':
                self.logger.info('Creating volume with {0} GB diskspace'.format(diskspace))
                try:
                    volume = self.conn.block_storage.create_volume(name=volumename, size=int(diskspace)).to_dict()
                except Exception as e:
                    self.logger.error(
                        'Trying to create volume with {0} GB for vm {1} error : {2}'.format(diskspace, servername, e),
                        exc_info=True)
                    raise ressourceException(Reason=str(e))
                volumeId = volume['id']
                with open('../../mount.sh', 'r') as file:
                    text = file.read()
                    text = text.replace('VOLUMEID', 'virtio-' + volumeId[0:20])
                    text = encodeutils.safe_encode(text.encode('utf-8'))
                init_script = base64.b64encode(text).decode('utf-8')

                server = self.conn.compute.create_server(
                    name=servername, image_id=image.id, flavor_id=flavor.id,
                    networks=[{"uuid": network.id}], key_name=keypair.name, metadata=metadata, user_data=init_script)
            else:
                server = self.conn.compute.create_server(
                    name=servername, image_id=image.id, flavor_id=flavor.id,
                    networks=[{"uuid": network.id}], key_name=keypair.name, metadata=metadata)

            return {'openstackid': server.to_dict()['id'], 'volumeId': volumeId}
        except Exception as e:
            self.logger.error('Start Server {1} error:{0}'.format(e, servername))
            return {}

    def create_volume(self, volume_name, diskspace):
        self.logger.info('Creating volume with {0} GB diskspace'.format(diskspace))
        try:
            volume = self.conn.block_storage.create_volume(name=volume_name, size=int(diskspace)).to_dict()
            volumeId = volume['id']
            return volumeId
        except Exception as e:
            self.logger.error(
                'Trying to create volume with {0} GB  error : {1}'.format(diskspace, e),
                exc_info=True)
            raise ressourceException(Reason=str(e))

    def attach_volume_to_server(self, openstack_id, volume_id):
        def checkStatusVolume(volume, conn):
            self.logger.info("Checking Status Volume {0}".format(volume_id))
            done = False
            while done == False:

                status = conn.block_storage.get_volume(volume).to_dict()['status']

                if status != 'available':

                    time.sleep(3)
                else:
                    done = True
                    time.sleep(2)
            return volume

        server = self.conn.compute.get_server(openstack_id)
        if server is None:
            self.logger.error("No Server  {0} ".format(openstack_id))
            raise serverNotFoundException(Reason='No Server {0}'.format(openstack_id))
        checkStatusVolume(volume_id, self.conn)

        self.logger.info('Attaching volume {0} to virtualmachine {1}'.format(volume_id, openstack_id))
        try:
            self.conn.compute.create_volume_attachment(server=server, volumeId=volume_id)
        except Exception as e:
            self.logger.error(
                'Trying to attache volume {0} to vm {1} error : {2}'.format(volume_id, openstack_id, e),
                exc_info=True)
            self.logger.info("Delete Volume  {0}".format(volume_id))
            conn.block_storage.delete_volume(volume=volume_id)
            return False

        return True

    def check_server_status(self, openstack_id, diskspace, volume_id):
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

        try:
            if serv['status'] == 'ACTIVE':
                host = self.get_server(openstack_id).floating_ip
                port = self.SSH_PORT

                if self.USE_JUMPHOST:
                    serv_cop = self.get_server(openstack_id)
                    server_base = serv_cop.fixed_ip.split(".")[-1]
                    host = str(self.JUMPHOST_IP)
                    port = int(self.JUMPHOST_BASE) + int(server_base) * 3
                elif self.get_server(openstack_id).floating_ip == None:
                    host = self.add_floating_ip_to_server(openstack_id, self.FLOATING_IP_NETWORK)
                if self.netcat(host, port) == True:
                    if diskspace > 0:
                        attached = self.attach_volume_to_server(openstack_id=openstack_id,
                                                                volume_id=volume_id)

                        if attached is False:
                            server = self.get_server(openstack_id)
                            self.delete_server(openstack_id=openstack_id)
                            server.status = 'DESTROYED'
                            return server
                        return self.get_server(openstack_id)
                    return self.get_server(openstack_id)
                else:
                    server = self.get_server(openstack_id)
                    server.status = 'PORT_CLOSED'
                    return server
            else:
                server = self.get_server(openstack_id)
                server.status = 'BUILD'
                return server
        except Exception as e:
            self.logger.error('Check Status VM {0} error: {1}'.format(openstack_id, e))
            return None

    def get_IP_PORT(self, openstack_id):
        self.logger.info("Get IP and PORT for server {0}".format(openstack_id))

        # check if jumphost is active
        try:
            if 'True' == str(self.USE_JUMPHOST):
                server = self.get_server(openstack_id)
                server_base = server.fixed_ip.split(".")[-1]
                port = int(self.JUMPHOST_BASE) + int(server_base) * 3
                return {'IP': str(self.JUMPHOST_IP), 'PORT': str(port)}

            else:
                floating_ip = self.get_server(openstack_id).floating_ip
                return {'IP': str(floating_ip)}
        except Exception as e:
            self.logger.error("Get IP and PORT for server {0} error:".format(openstack_id, e))
            return {}

    def create_snapshot(self, openstack_id, name, elixir_id, base_tag):
        self.logger.info(
            'Create Snapshot from Instance {0} with name {1} for {2}'.format(openstack_id, name, elixir_id))

        try:
            snapshot_munch = self.conn.create_image_snapshot(server=openstack_id, name=name)
        except Exception:
            self.logger.error("Instance {0} not found".format(openstack_id))
            return
        try:
            snapshot_id = snapshot_munch['id']
            self.conn.image.add_tag(image=snapshot_id, tag=elixir_id)
            self.conn.image.add_tag(image=snapshot_id, tag='snapshot_image:{0}'.format(base_tag))
            return snapshot_id
        except Exception as e:
            self.logger.error(
                'Create Snapshot from Instance {0} with name {1} for {2} error : {3}'.format(openstack_id, name,
                                                                                             elixir_id, e))
            return

    def delete_image(self, image_id):
        self.logger.info('Delete Image {0}'.format(image_id))
        try:
            image = self.conn.compute.get_image(image_id)
            if image is None:
                self.logger.error('Image {0} not found!'.format(image))
                raise imageNotFoundException(Reason=('Image {0} not found'.format(image)))
            self.conn.compute.delete_image(image)
            return True
        except Exception as e:
            self.logger.error('Delete Image {0} error : {1}'.format(image_id, e))
            return False

    def add_floating_ip_to_server(self, openstack_id, network):
        try:

            server = self.conn.compute.get_server(openstack_id)
            if server is None:
                self.logger.error("Instance {0} not found".format(openstack_id))
                raise serverNotFoundException
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
                        "Adding existing Floating IP {0} to {1}".format(str(floating_ip.floating_ip_address),
                                                                        openstack_id))
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
        except Exception as e:
            self.logger.error("Adding Floating IP to {0} with network {1} error:{2}".format(openstack_id, network, e))
            return

    def netcat(self, host, port):
        self.logger.info("Checking SSH Connection {0}:{1}".format(host, port))
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            r = sock.connect_ex((host, port))
            self.logger.info("Checking SSH Connection {0}:{1} Result = {2}".format(host, port, r))
            if r == 0:
                return True
            else:
                return False

    def delete_server(self, openstack_id):
        self.logger.info("Delete Server {0}".format(openstack_id))
        try:
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
            self.conn.compute.delete_server(server)

            return True
        except Exception as e:
            self.logger.error("Delete Server {0} error: {1}".format(openstack_id, e))
            return False

    def delete_volume_attachment(self, volume_id, server_id):
        try:
            attachments = self.conn.block_storage.get_volume(volume_id).attachments
            for attachment in attachments:
                volume_attachment_id = attachment['id']
                instance_id = attachment['server_id']
                if instance_id == server_id:
                    self.logger.info("Delete Volume Attachment  {0}".format(volume_attachment_id))
                    self.conn.compute.delete_volume_attachment(volume_attachment=volume_attachment_id, server=server_id)
            return True
        except Exception as e:
            self.logger.error("Delete Volume Attachment  {0} error: {1}".format(volume_attachment_id, e))
            return False

    def delete_volume(self, volume_id):
        def checkStatusVolume(volume, conn):
            self.logger.info("Checking Status Volume {0}".format(volume_id))
            done = False
            while done == False:

                status = conn.block_storage.get_volume(volume).to_dict()['status']

                if status != 'available':

                    time.sleep(3)
                else:
                    done = True
            return volume

        try:
            checkStatusVolume(volume_id, self.conn)
            self.logger.info("Delete Volume  {0}".format(volume_id))
            self.conn.block_storage.delete_volume(volume=volume_id)
            return True
        except Exception as e:
            self.logger.error("Delete Volume {0} error".format(volume_id, e))
            return False

    def stop_server(self, openstack_id):
        self.logger.info("Stop Server {0}".format(openstack_id))
        server = self.conn.compute.get_server(openstack_id)
        try:
            if server is None:
                self.logger.error("Instance {0} not found".format(openstack_id))
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
        except Exception as e:
            self.logger.error("Stop Server {0} error:".format(openstack_id, e))

            return False

    def reboot_server(self, server_id, reboot_type):
        self.logger.info("Reboot Server {} {}".format(server_id, reboot_type))
        try:
            server = self.conn.compute.get_server(server_id)
            if server is None:
                self.logger.error("Instance {0} not found".format(server_id))
                raise serverNotFoundException
            else:
                self.conn.compute.reboot_server(server, reboot_type)
                return True
        except Exception as e:
            self.logger.info("Reboot Server {} {} Error : {}".format(server_id, reboot_type, e))
            return False

    def resume_server(self, openstack_id):

        self.logger.info("Resume Server {0}".format(openstack_id))
        try:
            server = self.conn.compute.get_server(openstack_id)
            if server is None:
                self.logger.error("Instance {0} not found".format(openstack_id))
                raise serverNotFoundException

            if server.status == 'SUSPENDED':
                self.conn.compute.resume_server(server)
                while server.status != 'ACTIVE':
                    server = self.conn.compute.get_server(server)
                    time.sleep(3)

                return True
            else:

                return False
        except Exception as e:
            self.logger.error("Resume Server {0} error:".format(openstack_id, e))
            return False

    def get_limits(self):
        self.logger.info("Get Limits")
        limits = self.conn.get_compute_limits()
        limits.update(self.conn.get_volume_limits())
        maxTotalVolumes = str(limits['absolute']['maxTotalVolumes'])
        maxTotalInstances = str(limits['max_total_instances'])
        maxTotalVolumeGigabytes = str(limits['absolute']['maxTotalVolumeGigabytes'])
        totalRamUsed = str(limits['total_ram_used'])
        totalInstancesUsed = str(limits['total_instances_used'])
        print(limits)
        return {'maxTotalVolumes': maxTotalVolumes, 'maxTotalVolumeGigabytes': maxTotalVolumeGigabytes,
                'maxTotalInstances': maxTotalInstances, 'totalRamUsed': totalRamUsed,
                'totalInstancesUsed': totalInstancesUsed}
