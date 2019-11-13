"""
This Module implements an VirtualMachineHandler.

Which can be used for the PortalClient.
"""

try:
    from VirtualMachineService import Iface
    from ttypes import serverNotFoundException
    from ttypes import imageNotFoundException
    from ttypes import networkNotFoundException
    from ttypes import authenticationException
    from ttypes import otherException
    from ttypes import flavorNotFoundException
    from ttypes import ressourceException
    from ttypes import Flavor, Image, VM, PlaybookResult
    from constants import VERSION
    from ancon.Playbook import Playbook

except Exception:
    from .VirtualMachineService import Iface
    from .ttypes import serverNotFoundException
    from .ttypes import imageNotFoundException
    from .ttypes import networkNotFoundException
    from .ttypes import authenticationException
    from .ttypes import otherException
    from .ttypes import flavorNotFoundException
    from .ttypes import ressourceException
    from .ttypes import Flavor, Image, VM, PlaybookResult
    from .constants import VERSION
    from .ancon.Playbook import Playbook

from openstack import connection
from openstack import exceptions
from deprecated import deprecated
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client
import socket
from contextlib import closing
import urllib
import os
import time
import datetime
import logging
import yaml
import base64
from oslo_utils import encodeutils
import redis
import parser

active_playbooks = dict()


class VirtualMachineHandler(Iface):
    """Handler which the PortalClient uses."""

    global active_playbooks
    BUILD = "BUILD"
    ACTIVE = "ACTIVE"
    PREPARE_PLAYBOOK_BUILD = "PREPARE_PLAYBOOK_BUILD"
    BUILD_PLAYBOOK = "BUILD_PLAYBOOK"
    PLAYBOOK_FAILED = "PLAYBOOK_FAILED"

    def keyboard_interrupt_handler_playbooks(self):
        global active_playbooks
        for k, v in active_playbooks.items():
            self.logger.info("Clearing traces of Playbook-VM for (openstack_id): {0}".format(k))
            self.delete_keypair(key_name=self.redis.hget(k, "name").decode("utf-8"))
            v.stop(k)
            self.delete_server(openstack_id=k)
        raise SystemExit(0)

    def create_connection(self):
        """
            Create connection to OpenStack.

            :return: OpenStack connection instance
            """
        try:

            conn = connection.Connection(
                username=self.USERNAME,
                password=self.PASSWORD,
                auth_url=self.AUTH_URL,
                project_name=self.PROJECT_NAME,
                user_domain_name=self.USER_DOMAIN_NAME,
                project_domain_id=self.PROJECT_DOMAIN_ID
            )
            conn.authorize()
        except Exception as e:
            self.logger.exception("Client failed authentication at Openstack : {0}", e)
            raise authenticationException(
                Reason="Client failed authentication at Openstack"
            )

        self.logger.info("Connected to Openstack")
        return conn

    def __init__(self, config):
        """
            Initialize the handler.

            Read all config variables and creates a connection to OpenStack.
            """
        # create logger with 'spam_application'
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        self.fh = logging.FileHandler("log/portal_client_debug.log")
        self.fh.setLevel(logging.DEBUG)
        # create console handler with a higher log level
        self.ch = logging.StreamHandler()
        self.ch.setLevel(logging.INFO)
        # create formatter and add it to the handlers
        self.formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.fh.setFormatter(self.formatter)
        self.ch.setFormatter(self.formatter)
        # add the handlers to the logger
        self.logger.addHandler(self.fh)
        self.logger.addHandler(self.ch)

        # connection to redis. Uses a pool with 10 connections.
        self.pool = redis.ConnectionPool(host='redis', port=6379)
        self.redis = redis.Redis(connection_pool=self.pool, charset='utf-8')

        self.USERNAME = os.environ["OS_USERNAME"]
        self.PASSWORD = os.environ["OS_PASSWORD"]
        self.PROJECT_NAME = os.environ["OS_PROJECT_NAME"]
        self.PROJECT_ID = os.environ["OS_PROJECT_ID"]
        self.USER_DOMAIN_NAME = os.environ["OS_USER_DOMAIN_NAME"]
        self.AUTH_URL = os.environ["OS_AUTH_URL"]
        self.PROJECT_DOMAIN_ID = os.environ["OS_PROJECT_DOMAIN_ID"]
        self.SSH_PORT = 22

        with open(config, "r") as ymlfile:
            cfg = yaml.load(ymlfile, Loader=yaml.SafeLoader)
            self.USE_GATEWAY = cfg["openstack_connection"]["use_gateway"]
            self.NETWORK = cfg["openstack_connection"]["network"]
            self.FLOATING_IP_NETWORK = cfg["openstack_connection"][
                "floating_ip_network"
            ]
            self.AVAIALABILITY_ZONE = cfg["openstack_connection"]["availability_zone"]
            self.DEFAULT_SECURITY_GROUP = cfg['openstack_connection']['default_security_group']
            if self.USE_GATEWAY:
                self.GATEWAY_IP = cfg["openstack_connection"]["gateway_ip"]
                self.SSH_FORMULAR = cfg["openstack_connection"]["ssh_port_calc_formular"]
                self.UDP_FORMULAR = cfg["openstack_connection"]["udp_port_calc_formular"]
                self.SSH_PORT_CALCULATION = parser.expr(self.SSH_FORMULAR).compile()
                self.UDP_PORT_CALCULATION = parser.expr(self.UDP_FORMULAR).compile()
                self.logger.info("Gateway IP is {}".format(self.GATEWAY_IP))

            if cfg["openstack_connection"]["openstack_default_security_group"]:
                self.OPENSTACK_DEFAULT_SECURITY_GROUP = cfg["openstack_connection"][
                    "openstack_default_security_group"]
            else:
                self.OPENSTACK_DEFAULT_SECURITY_GROUP = "default"

        self.conn = self.create_connection()

    @deprecated(version="1.0.0", reason="Not supported at the moment")
    def setUserPassword(self, user, password):
        """
            Set the password of a user.

            :param user: Elixir-Id of the user which wants to set a password
            :param password: The new password.
            :return: The new password
            """
        if str(self.SET_PASSWORD) == "True":
            try:
                auth = v3.Password(
                    auth_url=self.AUTH_URL,
                    username=self.USERNAME,
                    password=self.PASSWORD,
                    project_name=self.PROJECT_NAME,
                    user_domain_id="default",
                    project_domain_id="default",
                )

                sess = session.Session(auth=auth)

                def findUser(keystone, name):
                    users = keystone.users.list()
                    for user in users:
                        if user.__dict__["name"] == name:
                            return user

                keystone = client.Client(session=sess)
                user = findUser(keystone, user)
                keystone.users.update(user, password=password)
                return password
            except Exception as e:
                self.logger.exception(
                    "Set Password for user {0} failed : {1}".format(user, str(e))
                )
                return otherException(Reason=str(e))
        else:
            raise otherException(Reason="Not allowed")

    def get_Flavors(self):
        """
        Get Flavors.

        :return: List of flavor instances.
        """
        self.logger.info("Get Flavors")
        flavors = list()
        try:
            for flav in list(self.conn.list_flavors(get_extra=True)):
                flavor = Flavor(
                    vcpus=flav["vcpus"],
                    ram=flav["ram"],
                    disk=flav["disk"],
                    name=flav["name"],
                    openstack_id=flav["id"],
                    tags=list(flav["extra_specs"].keys()),
                )
                self.logger.info(flavor)
                flavors.append(flavor)
            return flavors
        except Exception as e:
            self.logger.exception("Get Flavors Error: {0}".format(e))
            return ()

    @deprecated(
        version="1.0.0",
        reason="Vers. of Denbi API Client and Portalclient won't be compared",
    )
    def check_Version(self, version):
        """
        Compare Version.

        :param version: Version to compare local version with
        :return:True if same version, False if not
        """
        self.logger.info(
            "Compare Version : Server Version = {0} "
            "|| Client Version = {1}".format(VERSION, version)
        )
        try:
            if version == VERSION:
                return True
            else:
                return False
        except Exception as e:
            self.logger.exception("Compare Version Error: {0}".format(e))
            return False

    def get_client_version(self):
        """
        Get client version.

        :return: Version of the client.
        """
        # self.logger.info("Get Version of Client: {}".format(VERSION))
        return str(VERSION)

    def get_Images(self):
        """
        Get Images.

        :return: List of image instances.
        """
        self.logger.info("Get Images")
        images = list()
        try:
            for img in filter(
                    lambda x: "tags" in x
                              and len(x["tags"]) > 0
                              and x["status"] == "active",
                    self.conn.list_images(),
            ):

                metadata = img["metadata"]
                description = metadata.get("description")
                tags = img.get("tags")
                image_type = img.get("image_type", "image")
                if description is None:
                    self.logger.warning("No Description and  for " + img["name"])

                image = Image(
                    name=img["name"],
                    min_disk=img["min_disk"],
                    min_ram=img["min_ram"],
                    status=img["status"],
                    created_at=img["created_at"],
                    updated_at=img["updated_at"],
                    openstack_id=img["id"],
                    description=description,
                    tag=tags,
                    is_snapshot=image_type == "snapshot"
                )
                self.logger.info(image)

                images.append(image)

            return images
        except Exception as e:
            self.logger.exception("Get Images Error: {0}".format(e))
            return ()

    def get_Image_with_Tag(self, id):
        """
        Get Image with Tags.

        :param id: Id of the image
        :return: Image instance
        """
        self.logger.info("Get Image {0} with tags".format(id))
        try:
            images = self.conn.list_images()
            img = list(filter(lambda image: image["id"] == id, images))[0]
            metadata = img["metadata"]
            description = metadata.get("description")
            tags = img.get("tags")
            image = Image(
                name=img["name"],
                min_disk=img["min_disk"],
                min_ram=img["min_ram"],
                status=img["status"],
                created_at=img["created_at"],
                updated_at=img["updated_at"],
                openstack_id=img["id"],
                description=description,
                tag=tags,
            )
            return image
        except Exception as e:
            self.logger.exception("Get Image {0} with Tag Error: {1}".format(id, e))
            return

    def delete_keypair(self, key_name):
        key_pair = self.conn.compute.find_keypair(key_name)
        if key_pair:
            self.conn.compute.delete_keypair(key_pair)

    def import_keypair(self, keyname, public_key):
        """
        Import Keypair to OpenStack.

        :param keyname: Name of the Key
        :param public_key: The Key
        :return: Created Keypair
        """
        try:
            keypair = self.conn.compute.find_keypair(keyname)
            if not keypair:
                self.logger.info("Create Keypair {0}".format(keyname))

                keypair = self.conn.compute.create_keypair(
                    name=keyname, public_key=public_key
                )
                return keypair
            elif keypair.public_key != public_key:
                self.logger.info("Key has changed. Replace old Key")
                self.conn.compute.delete_keypair(keypair)
                keypair = self.conn.compute.create_keypair(
                    name=keyname, public_key=public_key
                )
                return keypair
            return keypair
        except Exception as e:
            self.logger.exception("Import Keypair {0} error:{1}".format(keyname, e))
            return

    def get_server(self, openstack_id):
        """
        Get a server.

        :param openstack_id: Id of the server
        :return: Server instance
        """
        floating_ip = None
        fixed_ip = None
        self.logger.info("Get Server {0}".format(openstack_id))
        try:
            server = self.conn.compute.get_server(openstack_id)
        except Exception as e:
            self.logger.exception("No Server found {0} | Error {1}".format(openstack_id, e))
            return VM(status="DELETED")
        if server is None:
            self.logger.exception("No Server  {0}".format(openstack_id))
            raise serverNotFoundException(Reason="No Server {0}".format(openstack_id))
        serv = server.to_dict()

        if serv["attached_volumes"]:
            volume_id = serv["attached_volumes"][0]["id"]
            diskspace = self.conn.block_storage.get_volume(volume_id).to_dict()["size"]
        else:

            diskspace = 0
        if serv["launched_at"]:
            dt = datetime.datetime.strptime(
                serv["launched_at"][:-7], "%Y-%m-%dT%H:%M:%S"
            )
            timestamp = time.mktime(dt.timetuple())
        else:
            timestamp = None
        try:
            flav = self.conn.compute.get_flavor(serv["flavor"]["id"]).to_dict()
        except Exception as e:
            self.logger.exception(e)
            flav = None
        try:
            img = self.get_Image_with_Tag(serv["image"]["id"])
        except Exception as e:
            self.logger.exception(e)
            img = None
        for values in server.addresses.values():
            for address in values:

                if address["OS-EXT-IPS:type"] == "floating":
                    floating_ip = address["addr"]
                elif address["OS-EXT-IPS:type"] == "fixed":
                    fixed_ip = address["addr"]

        if floating_ip:
            server = VM(
                flav=Flavor(
                    vcpus=flav["vcpus"],
                    ram=flav["ram"],
                    disk=flav["disk"],
                    name=flav["name"],
                    openstack_id=flav["id"],
                ),
                img=img,
                status=serv["status"],
                metadata=serv["metadata"],
                project_id=serv["project_id"],
                keyname=serv["key_name"],
                openstack_id=serv["id"],
                name=serv["name"],
                created_at=str(timestamp),
                floating_ip=floating_ip,
                fixed_ip=fixed_ip,
                diskspace=diskspace,
            )
        else:
            server = VM(
                flav=Flavor(
                    vcpus=flav["vcpus"],
                    ram=flav["ram"],
                    disk=flav["disk"],
                    name=flav["name"],
                    openstack_id=flav["id"],
                ),
                img=img,
                status=serv["status"],
                metadata=serv["metadata"],
                project_id=serv["project_id"],
                keyname=serv["key_name"],
                openstack_id=serv["id"],
                name=serv["name"],
                created_at=str(timestamp),
                fixed_ip=fixed_ip,
                diskspace=diskspace,
            )
        return server

    def get_servers_by_ids(self, ids):
        servers = []
        for id in ids:
            try:
                servers.append(self.conn.compute.get_server(id))
            except:
                self.logger.error("Requested VM {} not found!".format(id))
                pass
        server_list = []
        for server in servers:
            server_list.append(self.openstack_server_to_thrift_server(server))
        return server_list

    def get_image(self, image):
        image = self.conn.compute.find_image(image)
        if image is None:
            self.logger.exception("Image {0} not found!".format(image))
            raise imageNotFoundException(
                Reason=("Image {0} not found".format(image))
            )
        return image

    def get_flavor(self, flavor):
        flavor = self.conn.compute.find_flavor(flavor)
        if flavor is None:
            self.logger.exception("Flavor {0} not found!".format(flavor))
            raise flavorNotFoundException(
                Reason="Flavor {0} not found!".format(flavor)
            )
        return flavor

    def get_network(self):
        network = self.conn.network.find_network(self.NETWORK)
        if network is None:
            self.logger.exception("Network {0} not found!".format(network))
            raise networkNotFoundException(
                Reason="Network {0} not found!".format(network)
            )
        return network

    def create_volume_by_start(self, volume_storage, volume_name, server_name, metadata):
        self.logger.info(
            "Creating volume with {0} GB diskspace".format(volume_storage)
        )
        try:
            volume = self.conn.block_storage.create_volume(
                name=volume_name, size=int(volume_storage), metadata=metadata
            ).to_dict()
        except Exception as e:
            self.logger.exception(
                "Trying to create volume with {0}"
                " GB for vm {1} error : {2}".format(volume_storage, server_name, e),
                exc_info=True,
            )
            raise ressourceException(Reason=str(e))
        return volume["id"]

    def create_mount_init_script(self, volume_id):
        fileDir = os.path.dirname(os.path.abspath(__file__))
        mount_script = os.path.join(fileDir, "scripts/bash/mount.sh")
        with open(mount_script, "r") as file:
            text = file.read()
            text = text.replace("VOLUMEID", "virtio-" + volume_id[0:20])
            text = encodeutils.safe_encode(text.encode("utf-8"))
        init_script = base64.b64encode(text).decode("utf-8")
        return init_script

    def create_volume(self, volume_name, diskspace, metadata):
        """
        Create volume.
        :param volume_name: Name of volume
        :param diskspace: Diskspace in GB for new volume
        :return: Id of new volume
        """
        self.logger.info("Creating volume with {0} GB diskspace".format(diskspace))
        try:
            volume = self.conn.block_storage.create_volume(
                name=volume_name, size=int(diskspace), metadata=metadata
            ).to_dict()
            volumeId = volume["id"]
            return volumeId
        except Exception as e:
            self.logger.exception(
                "Trying to create volume with {0} GB  error : {1}".format(diskspace, e),
                exc_info=True,
            )

            raise ressourceException(Reason=str(e))

    def start_server(
            self,
            flavor,
            image,
            public_key,
            servername,
            metadata,
            diskspace,
            volumename,
    ):
        """
        Start a new Server.

        :param flavor: Name of flavor which should be used.
        :param image: Name of image which should be used
        :param public_key: Publickey which should be used
        :param servername: Name of the new server
        :param elixir_id: Elixir_id of the user who started a new server
        :param diskspace: Diskspace in GB for volume which should be created
        :param volumename: Name of the volume
        :return: {'openstackid': serverId, 'volumeId': volumeId}
        """
        volume_id = ''
        self.logger.info("Start Server {0}".format(servername))
        try:
            image = self.get_image(image=image)
            flavor = self.get_flavor(flavor=flavor)
            network = self.get_network()
            key_name = metadata.get("elixir_id")[:-18]
            public_key = urllib.parse.unquote(public_key)
            key_pair = self.import_keypair(key_name, public_key)

            if diskspace > "0":
                volume_id = self.create_volume_by_start(volume_storage=diskspace,
                                                        volume_name=volumename,
                                                        server_name=servername, metadata=metadata)
                init_script = self.create_mount_init_script(volume_id=volume_id)

                server = self.conn.compute.create_server(
                    name=servername,
                    image_id=image.id,
                    flavor_id=flavor.id,
                    networks=[{"uuid": network.id}],
                    key_name=key_pair.name,
                    metadata=metadata,
                    user_data=init_script,
                    availability_zone=self.AVAIALABILITY_ZONE,
                )
            else:
                server = self.conn.compute.create_server(
                    name=servername,
                    image_id=image.id,
                    flavor_id=flavor.id,
                    networks=[{"uuid": network.id}],
                    key_name=key_pair.name,
                    metadata=metadata,
                )

            openstack_id = server.to_dict()["id"]

            return {"openstackid": openstack_id, "volumeId": volume_id}
        except Exception as e:
            self.logger.exception("Start Server {1} error:{0}".format(e, servername))
            return {}

    def start_server_with_custom_key(self, flavor, image, servername, metadata, diskspace,
                                     volumename):

        """
        Start a new Server.

        :param flavor: Name of flavor which should be used.
        :param image: Name of image which should be used
        :param public_key: Publickey which should be used
        :param servername: Name of the new server
        :param elixir_id: Elixir_id of the user who started a new server
        :param diskspace: Diskspace in GB for volume which should be created
        :param volumename: Name of the volume
        :return: {'openstackid': serverId, 'volumeId': volumeId}
        """
        self.logger.info("Start Server {} with custom key".format(servername))
        volume_id = ''
        try:
            image = self.get_image(image=image)
            flavor = self.get_flavor(flavor=flavor)
            network = self.get_network()
            private_key = self.conn.create_keypair(name=servername).__dict__['private_key']
            if int(diskspace) > 0:
                volume_id = self.create_volume_by_start(volume_storage=diskspace,
                                                        volume_name=volumename,
                                                        server_name=servername, metadata=metadata)
                init_script = self.create_mount_init_script(volume_id=volume_id)

                server = self.conn.compute.create_server(
                    name=servername,
                    image_id=image.id,
                    flavor_id=flavor.id,
                    networks=[{"uuid": network.id}],
                    key_name=servername,
                    metadata=metadata,
                    user_data=init_script,
                    availability_zone=self.AVAIALABILITY_ZONE,
                )
            else:
                server = self.conn.compute.create_server(
                    name=servername,
                    image_id=image.id,
                    flavor_id=flavor.id,
                    networks=[{"uuid": network.id}],
                    key_name=servername,
                    metadata=metadata,
                )

            openstack_id = server.to_dict()["id"]
            self.redis.hmset(openstack_id, dict(key=private_key, name=servername,
                                                status=self.PREPARE_PLAYBOOK_BUILD))
            return {"openstackid": openstack_id, "volumeId": volume_id, 'private_key': private_key}
        except Exception as e:
            self.delete_keypair(key_name=servername)
            self.logger.exception("Start Server {1} error:{0}".format(e, servername))
            return {}

    def create_and_deploy_playbook(self, public_key, playbooks_information, openstack_id):
        global active_playbooks
        self.logger.info(msg="Starting Playbook for (openstack_id): {0}"
                         .format(openstack_id))
        fields = self.get_ip_ports(openstack_id=openstack_id)
        key = self.redis.hget(openstack_id, "key").decode('utf-8')
        playbook = Playbook(fields["IP"],
                            fields["PORT"],
                            playbooks_information,
                            key,
                            public_key,
                            self.logger,
                            self.pool)
        self.redis.hset(openstack_id, "status", self.BUILD_PLAYBOOK)
        playbook.run_it()
        active_playbooks[openstack_id] = playbook
        return 0

    def exist_server(self, name):
        if self.conn.compute.find_server(name) is not None:
            return True
        else:
            return False

    def get_playbook_logs(self, openstack_id):
        global active_playbooks
        if self.redis.exists(openstack_id) == 1 and openstack_id in active_playbooks:
            key_name = self.redis.hget(openstack_id, 'name').decode('utf-8')
            playbook = active_playbooks.pop(openstack_id)
            status, stdout, stderr = playbook.get_logs()
            playbook.cleanup(openstack_id)
            self.delete_keypair(key_name=key_name)
            return PlaybookResult(status=status, stdout=stdout, stderr=stderr)
        else:
            return PlaybookResult(status=-2, stdout='', stderr='')

    def attach_volume_to_server(self, openstack_id, volume_id):
        """
        Attach volume to server.

        :param openstack_id: Id of server
        :param volume_id: Id of volume
        :return: True if attached, False if not
        """

        def checkStatusVolume(volume, conn):
            self.logger.info("Checking Status Volume {0}".format(volume_id))
            done = False
            while not done:

                status = conn.block_storage.get_volume(volume).to_dict()["status"]
                self.logger.info("Volume {} Status:{}".format(volume_id, status))
                if status == "in-use":
                    return False

                if status != "available":

                    time.sleep(3)
                else:
                    done = True
                    time.sleep(2)
            return True

        server = self.conn.compute.get_server(openstack_id)
        if server is None:
            self.logger.exception("No Server  {0} ".format(openstack_id))
            raise serverNotFoundException(Reason="No Server {0}".format(openstack_id))
        if checkStatusVolume(volume_id, self.conn):

            self.logger.info(
                "Attaching volume {0} to virtualmachine {1}".format(
                    volume_id, openstack_id
                )
            )
            try:
                self.conn.compute.create_volume_attachment(
                    server=server, volumeId=volume_id
                )
            except Exception as e:
                self.logger.exception(
                    "Trying to attache volume {0} to vm {1} error : {2}".format(
                        volume_id, openstack_id, e
                    ),
                    exc_info=True,
                )
                return False

            return True
        return True

    def check_server_status(self, openstack_id, diskspace, volume_id):
        """
        Check status of server.

        :param openstack_id: Id of server
        :param diskspace: diskspace of server(volume will be attached if server
                is active and diskpace >0)
        :param volume_id: Id of volume
        :return: server instance
        """
        # TODO: Remove diskspace param, if volume_id exist it can be attached
        # diskspace not need
        self.logger.info("Check Status VM {0}".format(openstack_id))
        try:
            server = self.conn.compute.get_server(openstack_id)
        except Exception:
            self.logger.exception("No Server with id  {0} ".format(openstack_id))
            return None
        if server is None:
            self.logger.exception("No Server with id {0} ".format(openstack_id))
            return None
        serv = server.to_dict()

        try:
            if serv["status"] == self.ACTIVE:
                host = self.get_server(openstack_id).floating_ip
                port = self.SSH_PORT

                if self.USE_GATEWAY:
                    serv_cop = self.get_server(openstack_id)
                    server_base = serv_cop.fixed_ip.split(".")[-1]
                    x = int(server_base)
                    host = str(self.GATEWAY_IP)
                    port = eval(self.SSH_PORT_CALCULATION)
                elif self.get_server(openstack_id).floating_ip is None:
                    host = self.add_floating_ip_to_server(
                        openstack_id, self.FLOATING_IP_NETWORK
                    )
                if self.netcat(host, port):
                    server = self.get_server(openstack_id)

                    if diskspace > 0:
                        attached = self.attach_volume_to_server(
                            openstack_id=openstack_id, volume_id=volume_id
                        )

                        if attached is False:
                            self.delete_server(openstack_id=openstack_id)
                            server.status = "DESTROYED"
                            return server

                    if self.redis.exists(openstack_id) == 1:
                        global active_playbooks
                        if openstack_id in active_playbooks:
                            playbook = active_playbooks[openstack_id]
                            playbook.check_status(openstack_id)
                        status = self.redis.hget(openstack_id, "status").decode('utf-8')
                        if status == self.PREPARE_PLAYBOOK_BUILD:
                            server.status = self.PREPARE_PLAYBOOK_BUILD
                            return server
                        elif status == self.BUILD_PLAYBOOK:
                            server.status = self.BUILD_PLAYBOOK
                            return server
                        elif status == self.PLAYBOOK_FAILED:
                            server.status = self.PLAYBOOK_FAILED
                            return server
                        else:
                            return server
                    return self.get_server(openstack_id)
                else:
                    server = self.get_server(openstack_id)
                    server.status = "PORT_CLOSED"
                    return server
            else:
                server = self.get_server(openstack_id)
                server.status = self.BUILD
                return server
        except Exception as e:
            self.logger.exception("Check Status VM {0} error: {1}".format(openstack_id, e))
            return None

    def openstack_server_to_thrift_server(self, server):
        serv = server.to_dict()
        fixed_ip = None
        floating_ip = None

        if serv["attached_volumes"]:
            volume_id = serv["attached_volumes"][0]["id"]
            diskspace = self.conn.block_storage.get_volume(volume_id).to_dict()["size"]
        else:
            diskspace = 0
        if serv["launched_at"]:
            dt = datetime.datetime.strptime(
                serv["launched_at"][:-7], "%Y-%m-%dT%H:%M:%S"
            )
            timestamp = time.mktime(dt.timetuple())
        else:
            timestamp = None
        try:
            flav = self.conn.compute.get_flavor(serv["flavor"]["id"]).to_dict()
        except Exception as e:
            self.logger.exception(e)
            flav = None
        try:
            img = self.get_Image_with_Tag(serv["image"]["id"])
        except Exception as e:
            self.logger.exception(e)
            img = None
        for values in server.addresses.values():
            for address in values:

                if address["OS-EXT-IPS:type"] == "floating":
                    floating_ip = address["addr"]
                elif address["OS-EXT-IPS:type"] == "fixed":
                    fixed_ip = address["addr"]

        server = VM(
            flav=Flavor(
                vcpus=flav["vcpus"],
                ram=flav["ram"],
                disk=flav["disk"],
                name=flav["name"],
                openstack_id=flav["id"],
            ),
            img=img,
            status=serv["status"],
            metadata=serv["metadata"],
            project_id=serv["project_id"],
            keyname=serv["key_name"],
            openstack_id=serv["id"],
            name=serv["name"],
            created_at=str(timestamp),
            fixed_ip=fixed_ip,
            floating_ip=floating_ip,
            diskspace=diskspace,
        )
        return server

    def get_servers(self):
        self.logger.info("Get all servers")
        servers = list(self.conn.compute.servers())
        server_list = []
        for server in servers:
            server_list.append(self.openstack_server_to_thrift_server(server))
        # self.logger.info(server_list)
        return server_list

    def add_security_group_to_server(self, http, https, udp, server_id):
        """
        Adds the default simple vm security group to the vm.
        Also adds a security group which can open http,https and udp ports.
        :param http: If http ports should be open
        :param https: If https ports should be open
        :param udp: If udp ports should be open
        :param server_id: The id of the server
        :return:
        """
        self.logger.info("Setting up security groups for {0}".format(server_id))
        if self.conn.network.find_security_group(server_id) is not None:
            self.logger.info("Security group with name {0} already exists. Returning from function.".format(server_id))
            return True

        standart_default_security_group = self.conn.network.find_security_group(
            name_or_id=self.OPENSTACK_DEFAULT_SECURITY_GROUP)
        default_security_group_simple_vm = self.conn.network.get_security_group(
            security_group=self.DEFAULT_SECURITY_GROUP)

        if standart_default_security_group:
            self.logger.info("Remove default OpenStack security from {}".format(server_id))

            self.conn.compute.remove_security_group_from_server(server=server_id,
                                                                security_group=standart_default_security_group)
        if default_security_group_simple_vm:
            self.logger.info(
                "Add default simple vm security group {} to {}".format(self.DEFAULT_SECURITY_GROUP,
                                                                       server_id))
            self.conn.compute.add_security_group_to_server(
                server=server_id, security_group=default_security_group_simple_vm
            )

        ip_base = \
            list(self.conn.compute.server_ips(server=server_id))[0].to_dict()['address'].split(".")[
                -1]
        x = int(ip_base)
        udp_port_start = eval(self.UDP_PORT_CALCULATION)

        security_group = self.conn.network.find_security_group(name_or_id=server_id)
        if security_group:
            self.conn.compute.remove_security_group_from_server(server=server_id,
                                                                security_group=security_group)
            self.conn.network.delete_security_group(security_group)

        security_group = self.create_security_group(
            name=server_id,
            udp_port_start=udp_port_start,
            udp=udp,
            ssh=True,
            https=https,
            http=http,
        )
        self.conn.compute.add_security_group_to_server(
            server=server_id, security_group=security_group
        )

        return True

    def get_ip_ports(self, openstack_id):
        """
        Get Ip and Port of the sever.

        :param openstack_id: Id of the server
        :return: {'IP': ip, 'PORT': port, 'UDP':start_port}
        """
        self.logger.info("Get IP and PORT for server {0}".format(openstack_id))

        # check if gateway is active
        try:
            if self.USE_GATEWAY:
                server = self.get_server(openstack_id)
                server_base = server.fixed_ip.split(".")[-1]
                x = int(server_base)
                port = eval(self.SSH_PORT_CALCULATION)
                udp_port_start = eval(self.UDP_PORT_CALCULATION)
                return {"IP": str(self.GATEWAY_IP), "PORT": str(port), "UDP": str(udp_port_start)}

            else:
                # todo security groups floating ips
                floating_ip = self.get_server(openstack_id)
                return {"IP": str(floating_ip)}
        except Exception as e:
            self.logger.exception(
                "Get IP and PORT for server {0} error:".format(openstack_id, e)
            )
            return {}

    def create_snapshot(self, openstack_id, name, elixir_id, base_tag, description):
        """
        Create an Snapshot from an server.

        :param openstack_id: Id of the server
        :param name: Name of the Snapshot
        :param elixir_id: Elixir Id of the user who requested the creation
        :param base_tag: Tag with which the servers image is also tagged
        :return: Id of the new Snapshot
        """
        self.logger.info(
            "Create Snapshot from Instance {0} with name {1} for {2}".format(
                openstack_id, name, elixir_id
            )
        )

        try:
            snapshot_munch = self.conn.create_image_snapshot(
                server=openstack_id, name=name
            )
        except Exception:
            self.logger.exception("Instance {0} not found".format(openstack_id))
            return
        try:
            snapshot = self.conn.get_image_by_id(snapshot_munch["id"])
            snapshot_id = snapshot["id"]
            # todo check again
            try:
                image = self.conn.get_image(name_or_id=snapshot_id)
                if description:
                    self.conn.update_image_properties(
                        image=image,
                        meta={'description': description})

                self.conn.image.add_tag(
                    image=snapshot_id, tag="snapshot_image:{0}".format(base_tag)
                )
            except Exception:
                self.logger.exception("Tag error catched")
                pass
            try:
                self.conn.image.add_tag(image=snapshot_id, tag=elixir_id)
            except Exception:
                pass

            return snapshot_id
        except Exception as e:
            self.logger.exception(
                "Create Snapshot from Instance {0}"
                " with name {1} for {2} error : {3}".format(
                    openstack_id, name, elixir_id, e
                )
            )
            return

    def delete_image(self, image_id):
        """
        Delete Image.

        :param image_id: Id of the image
        :return: True if deleted, False if not
        """
        self.logger.info("Delete Image {0}".format(image_id))
        try:
            image = self.conn.compute.get_image(image_id)
            if image is None:
                self.logger.exception("Image {0} not found!".format(image))
                raise imageNotFoundException(
                    Reason=("Image {0} not found".format(image))
                )
            self.conn.compute.delete_image(image)
            return True
        except Exception as e:
            self.logger.exception("Delete Image {0} error : {1}".format(image_id, e))
            return False

    def add_floating_ip_to_server(self, openstack_id, network):
        """
        Add a floating ip to a server.

        :param openstack_id: Id of the server
        :param network: Networkname which provides the floating ip
        :return: The floating ip
        """
        try:

            server = self.conn.compute.get_server(openstack_id)
            if server is None:
                self.logger.exception("Instance {0} not found".format(openstack_id))
                raise serverNotFoundException
            self.logger.info("Checking if Server already got an Floating Ip")
            for values in server.addresses.values():
                for address in values:
                    if address["OS-EXT-IPS:type"] == "floating":
                        return address["addr"]
            self.logger.info("Checking if unused Floating-Ip exist")

            for floating_ip in self.conn.network.ips():
                if not floating_ip.fixed_ip_address:
                    self.conn.compute.add_floating_ip_to_server(
                        server, floating_ip.floating_ip_address
                    )
                    self.logger.info(
                        "Adding existing Floating IP {0} to {1}".format(
                            str(floating_ip.floating_ip_address), openstack_id
                        )
                    )
                    return str(floating_ip.floating_ip_address)

            networkID = self.conn.network.find_network(network)
            if networkID is None:
                self.logger.exception("Network " + network + " not found")
                raise networkNotFoundException
            networkID = networkID.to_dict()["id"]
            floating_ip = self.conn.network.create_ip(floating_network_id=networkID)
            floating_ip = self.conn.network.get_ip(floating_ip)
            self.conn.compute.add_floating_ip_to_server(
                server, floating_ip.floating_ip_address
            )

            return floating_ip
        except Exception as e:
            self.logger.exception(
                "Adding Floating IP to {0} with network {1} error:{2}".format(
                    openstack_id, network, e
                )
            )
            return

    def netcat(self, host, port):
        """
        Try to connect to specific host:port.

        :param host: Host to connect
        :param port: Port to connect
        :return: True if successfully connected, False if not
        """
        self.logger.info("Checking SSH Connection {0}:{1}".format(host, port))
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            r = sock.connect_ex((host, port))
            self.logger.info(
                "Checking SSH Connection {0}:{1} Result = {2}".format(host, port, r)
            )
            if r == 0:
                return True
            else:
                return False

    def delete_server(self, openstack_id):
        """
        Delete Server.

        :param openstack_id: Id of the server
        :return: True if deleted, False if not
        """
        self.logger.info("Delete Server {0}".format(openstack_id))
        try:
            server = self.conn.compute.get_server(openstack_id)
            if server is None:
                self.logger.exception("Instance {0} not found".format(openstack_id))
                raise serverNotFoundException
            self.logger.info(server)
            self.logger.info(server.name)
            try:
                security_groups = self.conn.network.security_groups(name=openstack_id)
            except Exception as e:
                self.logger.exception(e)
            if security_groups is not None:
                for sg in security_groups:
                    self.logger.info("Delete security group {0}".format(openstack_id))
                    self.conn.compute.remove_security_group_from_server(server=server,
                                                                        security_group=sg)
                    self.conn.network.delete_security_group(sg)
                self.conn.compute.delete_server(server)
            else:
                return False

            return True
        except Exception as e:
            self.logger.exception("Delete Server {0} error: {1}".format(openstack_id, e))
            return False

    def delete_volume_attachment(self, volume_id, server_id):
        """
        Delete volume attachment.

        :param volume_id: Id of the attached volume
        :param server_id: Id of the server where the volume is attached
        :return: True if deleted, False if not
        """
        try:
            attachments = self.conn.block_storage.get_volume(volume_id).attachments
            for attachment in attachments:
                volume_attachment_id = attachment["id"]
                instance_id = attachment["server_id"]
                if instance_id == server_id:
                    self.logger.info(
                        "Delete Volume Attachment  {0}".format(volume_attachment_id)
                    )
                    self.conn.compute.delete_volume_attachment(
                        volume_attachment=volume_attachment_id, server=server_id
                    )
            return True
        except Exception as e:
            self.logger.exception(
                "Delete Volume Attachment  {0} error: {1}".format(
                    volume_attachment_id, e
                )
            )
            return False

    def delete_volume(self, volume_id):
        """
        Delete volume.

        :param volume_id: Id of the volume
        :return: True if deleted, False if not
        """

        def checkStatusVolume(volume, conn):
            self.logger.info("Checking Status Volume {0}".format(volume_id))
            done = False
            while not done:

                status = conn.block_storage.get_volume(volume).to_dict()["status"]

                if status != "available":

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
            self.logger.exception("Delete Volume {0} error".format(volume_id, e))
            return False

    def stop_server(self, openstack_id):
        """
        Stop server.

        :param openstack_id: Id of the server.
        :return: True if resumed, False if not
        """
        self.logger.info("Stop Server {0}".format(openstack_id))
        server = self.conn.compute.get_server(openstack_id)
        try:
            if server is None:
                self.logger.exception("Instance {0} not found".format(openstack_id))
                raise serverNotFoundException

            if server.status == "ACTIVE":
                self.conn.compute.stop_server(server)
                return True
            else:
                return False
        except Exception as e:
            self.logger.exception("Stop Server {0} error:".format(openstack_id, e))

            return False

    def reboot_server(self, server_id, reboot_type):
        """
        Reboot server.

        :param server_id: Id of the server
        :param reboot_type: HARD or SOFT
        :return:  True if resumed, False if not
        """
        self.logger.info("Reboot Server {} {}".format(server_id, reboot_type))
        try:
            server = self.conn.compute.get_server(server_id)
            if server is None:
                self.logger.exception("Instance {0} not found".format(server_id))
                raise serverNotFoundException
            else:
                self.conn.compute.reboot_server(server, reboot_type)
                return True
        except Exception as e:
            self.logger.exception(
                "Reboot Server {} {} Error : {}".format(server_id, reboot_type, e)
            )
            return False

    def resume_server(self, openstack_id):
        """
        Resume stopped server.

        :param openstack_id: Id of the server.
        :return: True if resumed, False if not
        """
        self.logger.info("Resume Server {0}".format(openstack_id))
        try:
            server = self.conn.compute.get_server(openstack_id)
            if server is None:
                self.logger.exception("Instance {0} not found".format(openstack_id))
                raise serverNotFoundException
            if server.status == "SHUTOFF":
                self.conn.compute.start_server(server)
                return True
            else:
                return False
        except Exception as e:
            self.logger.exception("Resume Server {0} error:".format(openstack_id, e))
            return False

    def create_security_group(
            self, name, udp_port_start=None, ssh=True, http=False, https=False, udp=False
    ):
        self.logger.info("Create new security group {}".format(name))
        new_security_group = self.conn.network.create_security_group(name=name)
        if http:
            self.logger.info("Add http rule to security group {}".format(name))
            self.conn.network.create_security_group_rule(
                direction="ingress",
                protocol="tcp",
                port_range_max=80,
                port_range_min=80,
                security_group_id=new_security_group["id"],
            )
            self.conn.network.create_security_group_rule(
                direction="ingress",
                ether_type="IPv6",
                protocol="tcp",
                port_range_max=80,
                port_range_min=80,
                security_group_id=new_security_group["id"],
            )

        if https:
            self.logger.info("Add https rule to security group {}".format(name))

            self.conn.network.create_security_group_rule(
                direction="ingress",
                protocol="tcp",
                port_range_max=443,
                port_range_min=443,
                security_group_id=new_security_group["id"],
            )
            self.conn.network.create_security_group_rule(
                direction="ingress",
                ether_type="IPv6",
                protocol="tcp",
                port_range_max=443,
                port_range_min=443,
                security_group_id=new_security_group["id"],
            )
        if udp:
            self.logger.info(
                "Add udp rule ports {} - {} to security group {}".format(
                    udp_port_start, udp_port_start + 9, name
                )
            )

            self.conn.network.create_security_group_rule(
                direction="ingress",
                protocol="udp",
                port_range_max=udp_port_start + 9,
                port_range_min=udp_port_start,
                security_group_id=new_security_group["id"],
            )
            self.conn.network.create_security_group_rule(
                direction="ingress",
                ether_type="IPv6",
                protocol="udp",
                port_range_max=udp_port_start + 9,
                port_range_min=udp_port_start,
                security_group_id=new_security_group["id"],
            )
        if ssh:
            self.logger.info("Add ssh rule to security group {}".format(name))

            self.conn.network.create_security_group_rule(
                direction="ingress",
                protocol="tcp",
                port_range_max=22,
                port_range_min=22,
                security_group_id=new_security_group["id"],
            )
            self.conn.network.create_security_group_rule(
                direction="ingress",
                ether_type="IPv6",
                protocol="tcp",
                port_range_max=22,
                port_range_min=22,
                security_group_id=new_security_group["id"],
            )

        return new_security_group

    def get_limits(self):
        """
        Get the Limits.

        (maxTotalVolumes,maxTotalVolumeGigabytes,
        maxTotalInstances,totalRamUsed,totalInstancesUsed)
        of the OpenStack Project from the Client.

        :return: {'maxTotalVolumes': maxTotalVolumes, '
                maxTotalVolumeGigabytes': maxTotalVolumeGigabytes,
                'maxTotalInstances': maxTotalInstances,
                 'totalRamUsed': totalRamUsed,
                'totalInstancesUsed': totalFlInstancesUsed}
        """
        self.logger.info("Get Limits")
        limits = self.conn.get_compute_limits()
        limits.update(self.conn.get_volume_limits())
        maxTotalVolumes = str(limits["absolute"]["maxTotalVolumes"])
        maxTotalInstances = str(limits["max_total_instances"])
        maxTotalVolumeGigabytes = str(limits["absolute"]["maxTotalVolumeGigabytes"])
        totalRamUsed = str(limits["total_ram_used"])
        totalInstancesUsed = str(limits["total_instances_used"])
        return {
            "maxTotalVolumes": maxTotalVolumes,
            "maxTotalVolumeGigabytes": maxTotalVolumeGigabytes,
            "maxTotalInstances": maxTotalInstances,
            "totalRamUsed": totalRamUsed,
            "totalInstancesUsed": totalInstancesUsed,
        }
