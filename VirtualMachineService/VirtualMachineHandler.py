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
    from ttypes import Flavor, Image, VM, PlaybookResult, Backend, ClusterInfo,Volume
    from constants import VERSION
    from ancon.Playbook import Playbook, THEIA, GUACAMOLE, ALL_TEMPLATES, RSTUDIO, JUPYTERNOTEBOOK

except Exception:
    from .VirtualMachineService import Iface
    from .ttypes import serverNotFoundException
    from .ttypes import imageNotFoundException
    from .ttypes import networkNotFoundException
    from .ttypes import authenticationException
    from .ttypes import otherException
    from .ttypes import flavorNotFoundException
    from .ttypes import ressourceException
    from .ttypes import Flavor, Image, VM, PlaybookResult, Backend, ClusterInfo,Volume
    from .constants import VERSION
    from .ancon.Playbook import Playbook, THEIA, GUACAMOLE, ALL_TEMPLATES, RSTUDIO, JUPYTERNOTEBOOK

import base64
import datetime
import logging
import os
import parser
import socket
import time
import urllib
from contextlib import closing

import redis
import requests as req
import yaml
from deprecated import deprecated
from keystoneauth1 import session
from keystoneauth1.identity import v3
from keystoneclient.v3 import client
from openstack import connection
from oslo_utils import encodeutils
from requests.exceptions import Timeout

active_playbooks = dict()


class VirtualMachineHandler(Iface):
    """Handler which the PortalClient uses."""

    global active_playbooks
    BUILD = "BUILD"
    ACTIVE = "ACTIVE"
    ERROR = "ERROR"
    PREPARE_PLAYBOOK_BUILD = "PREPARE_PLAYBOOK_BUILD"
    BUILD_PLAYBOOK = "BUILD_PLAYBOOK"
    PLAYBOOK_FAILED = "PLAYBOOK_FAILED"
    DEFAULT_SECURITY_GROUP = 'defaultSimpleVM'
    DEFAULT_SECURITY_GROUPS = [DEFAULT_SECURITY_GROUP]

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
            # try to initialize forc connection
            try:
                self.BIBIGRID_URL = cfg["bibigrid"]["bibigrid_url"]
                self.SUB_NETWORK = cfg["bibigrid"]["sub_network"]
                self.logger.info(msg="Bibigrd url loaded: {0}".format(self.BIBIGRID_URL))
            except Exception as e:
                self.logger.exception(e)
                self.logger.info("Bibigrid not loaded.")
                self.BIBIGRID_URL = None
                self.SUB_NETWORK = None

            try:
                self.RE_BACKEND_URL = cfg["forc"]["forc_url"]
                self.FORC_API_KEY = os.environ["FORC_API_KEY"]
                self.FORC_ALLOWED = cfg["forc"]["forc_allowed"]
                self.logger.info(msg="Forc-Backend url loaded: {0}".format(self.RE_BACKEND_URL))
                self.logger.info("Client allows following research environments and respective versions: {0}".format(self.FORC_ALLOWED))
            except Exception as e:
                self.logger.exception(e)
                self.logger.info("Forc-Backend not loaded.")
                self.RE_BACKEND_URL = None
                self.FORC_API_KEY = None
                self.FORC_ALLOWED = None
            if self.USE_GATEWAY:
                self.GATEWAY_IP = cfg["openstack_connection"]["gateway_ip"]
                self.SSH_FORMULAR = cfg["openstack_connection"]["ssh_port_calc_formular"]
                self.UDP_FORMULAR = cfg["openstack_connection"]["udp_port_calc_formular"]
                self.SSH_PORT_CALCULATION = parser.expr(self.SSH_FORMULAR).compile()
                self.UDP_PORT_CALCULATION = parser.expr(self.UDP_FORMULAR).compile()
                self.logger.info("Gateway IP is {}".format(self.GATEWAY_IP))

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
                self.logger.info(set(ALL_TEMPLATES).intersection(tags))
                if len(set(ALL_TEMPLATES).intersection(tags)) > 0 and not self.cross_check_forc_image(tags):
                    self.logger.info("Resenv check: Skipping {0}.".format(img["name"]))
                    continue
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
            img = self.conn.get_image(name_or_id=id)
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
            return None

    def get_Images_by_filter(self, filter_list):
        """
        Get filtered Images.

        :return: List of image instances.
        """
        self.logger.info("Get filtered Images: {0}".format(filter_list))
        images = list()
        try:
            for img in filter(
                    lambda x: "tags" in x
                              and len(x["tags"]) > 0
                              and x["status"] == "active",
                    self.conn.list_images(),
            ):
                tags = img.get("tags")
                if "resenv" in filter_list:
                    modes = filter_list["resenv"].split(",")
                    self.logger.info(modes)
                    if "resenv" in tags and not self.cross_check_forc_image(tags):
                        continue
                metadata = img["metadata"]
                description = metadata.get("description")
                image_type = img.get("image_type", "image")
                if description is None:
                    self.logger.warning("No Description for {0}".format(img["name"]))

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

    def openstack_flav_to_thrift_flav(self, flavor):
        try:
            if "id" in flavor:
                flavor = self.conn.compute.get_flavor(flavor["id"]).to_dict()
                name = flavor["name"]
                openstack_id = flavor["id"]
            else:
                # Giessen
                name = flavor["original_name"]
                openstack_id = None

            flav = Flavor(
                vcpus=flavor["vcpus"],
                ram=flavor["ram"],
                disk=flavor["disk"],
                name=name,
                openstack_id=openstack_id,
            )
            return flav
        except Exception as e:
            self.logger.exception(e)
            flav = Flavor(
                vcpus=None,
                ram=None,
                disk=None,
                name=None,
                openstack_id=None,
            )
            return flav

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

        flav = self.openstack_flav_to_thrift_flav(serv["flavor"])

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
                flav=flav,
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
                flav=flav,
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
            self.logger.info("Get server {}".format(id))
            try:
                server = self.conn.get_server_by_id(id)
                servers.append(server)
            except Exception as e:
                self.logger.exception("Requested VM {} not found!\n {}".format(id, e))
                pass
        server_list = []
        for server in servers:
            if server:
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
            https,
            http,
            resenv
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
        :param http: bool for http rule in security group
        :param https: bool for https rule in security group
        :param resenv: array with names of requested resenvs
        :return: {'openstackid': serverId, 'volumeId': volumeId}
        """
        volume_id = ''
        self.logger.info("Start Server {0}".format(servername))
        custom_security_groups = []
        try:
            image = self.get_image(image=image)
            flavor = self.get_flavor(flavor=flavor)
            network = self.get_network()
            key_name = metadata.get("elixir_id")[:-18]
            public_key = urllib.parse.unquote(public_key)
            key_pair = self.import_keypair(key_name, public_key)

            custom_security_groups.append(
                self.create_security_group(name=servername + "_ssh", description="Only SSH").name)

            if http or https:
                custom_security_groups.append(self.create_security_group(
                    name=servername + '_https',
                    http=http, https=https,
                    description="Http/Https").name)

            if THEIA in resenv:
                custom_security_groups.append(self.create_security_group(
                    name=servername + "_theiaide", resenv=resenv, description="Theiaide", ssh=False
                ).name)
            if GUACAMOLE in resenv:
                custom_security_groups.append(self.create_security_group(
                    name=servername + "_guacamole", resenv=resenv, description="Guacamole",
                    ssh=False
                ).name)
            if RSTUDIO in resenv:
                custom_security_groups.append(self.create_security_group(
                    name=servername + "_rstudio", resenv=resenv, description="Rstudio",
                    ssh=False
                ).name)
            if JUPYTERNOTEBOOK in resenv:
                custom_security_groups.append(self.create_security_group(
                    name=servername + "_jupyternotebook", resenv=resenv, description="Jupyter Notebook",
                    ssh=False
                ).name)

            if diskspace > "0":
                volume_id = self.create_volume_by_start(volume_storage=diskspace,
                                                        volume_name=volumename,
                                                        server_name=servername, metadata=metadata)
                init_script = self.create_mount_init_script(volume_id=volume_id)

                server = self.conn.create_server(
                    name=servername,
                    image=image.id,
                    flavor=flavor.id,
                    network=[network.id],
                    key_name=key_pair.name,
                    meta=metadata,
                    userdata=init_script,
                    availability_zone=self.AVAIALABILITY_ZONE,
                    security_groups=self.DEFAULT_SECURITY_GROUPS + custom_security_groups

                )
            else:
                server = self.conn.create_server(
                    name=servername,
                    image=image.id,
                    flavor=flavor.id,
                    network=[network.id],
                    key_name=key_pair.name,
                    meta=metadata,
                    availability_zone=self.AVAIALABILITY_ZONE,
                    security_groups=self.DEFAULT_SECURITY_GROUPS + custom_security_groups
                )

            openstack_id = server['id']

            return {"openstackid": openstack_id, "volumeId": volume_id}
        except Exception as e:
            for security_group in custom_security_groups:
                self.conn.network.delete_security_group(security_group)
            self.logger.exception("Start Server {1} error:{0}".format(e, servername))
            return {}

    def start_server_with_custom_key(self, flavor, image, servername, metadata, diskspace,
                                     volumename, http, https, resenv):

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
        custom_security_groups = []

        try:
            image = self.get_image(image=image)
            flavor = self.get_flavor(flavor=flavor)
            network = self.get_network()
            key_creation = self.conn.create_keypair(name=servername)

            custom_security_groups.append(
                self.create_security_group(name=servername + "_ssh", description="Only SSH").name)

            if http or https:
                custom_security_groups.append(self.create_security_group(
                    name=servername + '_https',
                    http=http, https=https,
                    description="Http/Https").name)

            if THEIA in resenv:
                custom_security_groups.append(self.create_security_group(
                    name=servername + "_theiaide", resenv=resenv, description="Theiaide", ssh=False
                ).name)
            if GUACAMOLE in resenv:
                custom_security_groups.append(self.create_security_group(
                    name=servername + "_guacamole", resenv=resenv, description="Guacamole",
                    ssh=False
                ).name)
            if RSTUDIO in resenv:
                custom_security_groups.append(self.create_security_group(
                    name=servername + "_rstudio", resenv=resenv, description="Rstudio",
                    ssh=False
                ).name)
            if JUPYTERNOTEBOOK in resenv:
                custom_security_groups.append(self.create_security_group(
                    name=servername + "_jupyternotebook", resenv=resenv, description="Jupyter Notebook",
                    ssh=False
                ).name)

            try:
                private_key = key_creation["private_key"]
            except Exception:
                private_key = key_creation.__dict__["private_key"]

            if int(diskspace) > 0:
                volume_id = self.create_volume_by_start(volume_storage=diskspace,
                                                        volume_name=volumename,
                                                        server_name=servername, metadata=metadata)
                init_script = self.create_mount_init_script(volume_id=volume_id)

                server = self.conn.create_server(
                    name=servername,
                    image=image.id,
                    flavor=flavor.id,
                    network=[network.id],
                    key_name=servername,
                    meta=metadata,
                    userdata=init_script,
                    availability_zone=self.AVAIALABILITY_ZONE,
                    security_groups=self.DEFAULT_SECURITY_GROUPS + custom_security_groups
                )
            else:
                server = self.conn.create_server(
                    name=servername,
                    image=image.id,
                    flavor=flavor.id,
                    network=[network.id],
                    key_name=servername,
                    meta=metadata,

                    availability_zone=self.AVAIALABILITY_ZONE,
                    security_groups=self.DEFAULT_SECURITY_GROUPS + custom_security_groups
                )

            openstack_id = server['id']

            self.redis.hmset(openstack_id, dict(key=private_key, name=servername,
                                                status=self.PREPARE_PLAYBOOK_BUILD))
            return {"openstackid": openstack_id, "volumeId": volume_id, 'private_key': private_key}
        except Exception as e:
            self.delete_keypair(key_name=servername)
            for security_group in custom_security_groups:
                self.conn.network.delete_security_group(security_group)
            self.logger.exception("Start Server {1} error:{0}".format(e, servername))
            return {}

    def create_and_deploy_playbook(self, public_key, playbooks_information, openstack_id):
        global active_playbooks
        self.logger.info(msg="Starting Playbook for (openstack_id): {0}"
                         .format(openstack_id))
        port = self.get_vm_ports(openstack_id=openstack_id)
        key = self.redis.hget(openstack_id, "key").decode('utf-8')
        playbook = Playbook(self.GATEWAY_IP,
                            port["port"],
                            playbooks_information,
                            key,
                            public_key,
                            self.logger,
                            self.pool)
        self.redis.hset(openstack_id, "status", self.BUILD_PLAYBOOK)
        playbook.run_it()
        active_playbooks[openstack_id] = playbook
        return 0

    def has_forc(self):
        return self.RE_BACKEND_URL is not None

    def get_forc_url(self):
        url = self.RE_BACKEND_URL.split(':5000', 1)[0]
        return "{0}/".format(url)

    def cross_check_forc_image(self, tags):
        get_url = "{0}templates/".format(self.RE_BACKEND_URL)
        try:
            response = req.get(get_url, timeout=(30, 30), headers={"X-API-KEY": self.FORC_API_KEY})
            if response.status_code != 200:
                return ()
            else:
                templates = response.json()
        except Exception as e:
            self.logger.error("Could not get templates from FORC.\n {0}".format(e))
        cross_tags = list(set(ALL_TEMPLATES).intersection(tags))
        for template_dict in templates:
            if template_dict["name"] in self.FORC_ALLOWED and template_dict["name"] in cross_tags:
                if template_dict["version"] in self.FORC_ALLOWED[template_dict["name"]]:
                    return True
        return False

    def create_backend(self, elixir_id, user_key_url, template, upstream_url):
        template_version = self.get_template_version_for(template)
        if template_version is None:
            self.logger.warning("No suitable template version found for {0}. Aborting backend creation!"
                                .format(template))
            return {}
        try:
            post_url = "{0}backends/".format(self.RE_BACKEND_URL)
            backend_info = {
                "owner": elixir_id,
                "user_key_url": user_key_url,
                "template": template,
                "template_version": template_version,
                "upstream_url": upstream_url
            }
        except Exception as e:
            self.logger.exception(e)
            return {}
        try:
            response = req.post(post_url, json=backend_info, timeout=(30, 30),
                                headers={"X-API-KEY": self.FORC_API_KEY})
            try:
                data = response.json()
            except Exception as e:
                self.logger.exception(e)
                return {}
            return Backend(id=data["id"],
                           owner=data["owner"],
                           location_url=data["location_url"],
                           template=data["template"],
                           template_version=data["template_version"])
        except Timeout as e:
            self.logger.info(msg="create_backend timed out. {0}".format(e))
            return {}
        except Exception as e:
            self.logger.exception(e)
            return {}

    def get_backends(self):
        get_url = "{0}/backends/".format(self.RE_BACKEND_URL)
        try:
            response = req.get(get_url, timeout=(30, 30), headers={"X-API-KEY": self.FORC_API_KEY})
            if response.status_code == 401:
                return [response.json()]
            else:
                backends = []
                for data in response.json():
                    backends.append(Backend(id=data["id"],
                                            owner=data["owner"],
                                            location_url=data["location_url"],
                                            template=data["template"],
                                            template_version=data["template_version"]))
                return backends
        except Timeout as e:
            self.logger.info(msg="create_backend timed out. {0}".format(e))

    def get_backends_by_owner(self, elixir_id):
        get_url = "{0}/backends/byOwner/{1}".format(self.RE_BACKEND_URL, elixir_id)
        try:
            response = req.get(get_url, timeout=(30, 30), headers={"X-API-KEY": self.FORC_API_KEY})
            if response.status_code == 401:
                return [response.json()]
            else:
                backends = []
                for data in response.json():
                    backends.append(Backend(id=data["id"],
                                            owner=data["owner"],
                                            location_url=data["location_url"],
                                            template=data["template"],
                                            template_version=data["template_version"]))
                return backends
        except Timeout as e:
            self.logger.info(msg="create_backend timed out. {0}".format(e))

    def get_backends_by_template(self, template):
        get_url = "{0}/backends/byTemplate/{1}".format(self.RE_BACKEND_URL, template)
        try:
            response = req.get(get_url, timeout=(30, 30), headers={"X-API-KEY": self.FORC_API_KEY})
            if response.status_code == 401:
                return [response.json()]
            else:
                backends = []
                for data in response.json():
                    backends.append(Backend(id=data["id"],
                                            owner=data["owner"],
                                            location_url=data["location_url"],
                                            template=data["template"],
                                            template_version=data["template_version"]))
                return backends
        except Timeout as e:
            self.logger.info(msg="create_backend timed out. {0}".format(e))

    def get_backend_by_id(self, id):
        get_url = "{0}/backends/{1}".format(self.RE_BACKEND_URL, id)
        try:
            response = req.get(get_url, timeout=(30, 30), headers={"X-API-KEY": self.FORC_API_KEY})
            try:
                data = response.json()
            except Exception as e:
                self.logger.exception(e)
                return {}
            return Backend(id=data["id"],
                           owner=data["owner"],
                           location_url=data["location_url"],
                           template=data["template"],
                           template_version=data["template_version"])
        except Timeout as e:
            self.logger.info(msg="create_backend timed out. {0}".format(e))

    def delete_backend(self, id):
        delete_url = "{0}/backends/{1}".format(self.RE_BACKEND_URL, id)
        try:
            response = req.delete(delete_url, timeout=(30, 30),
                                  headers={"X-API-KEY": self.FORC_API_KEY})
            if response.status_code != 200:
                return str(response.json())
            elif response.status_code == 200:
                return str(True)
        except Timeout as e:
            self.logger.info(msg="create_backend timed out. {0}".format(e))
            return str(-1)
        except Exception as e:
            self.logger.exception(e)
            return str(-1)

    def exist_server(self, name):
        if self.conn.compute.find_server(name) is not None:
            return True
        else:
            return False

    def get_template_version_for(self, template):
        all_templates = self.get_templates()
        for template_version in self.FORC_ALLOWED[template]:
            for template_dict in all_templates:
                if template_dict["name"] == template:
                    if template_version == template_dict["version"]:
                        return template_version
        return None

    def cross_check_templates(self, templates):
        return_templates = set()
        for template_dict in templates:
            if template_dict["name"] in self.FORC_ALLOWED:
                if template_dict["version"] in self.FORC_ALLOWED[template_dict["name"]]:
                    return_templates.add(template_dict["name"])
        return return_templates

    def get_templates(self):
        get_url = "{0}templates/".format(self.RE_BACKEND_URL)
        try:
            response = req.get(get_url, timeout=(30, 30), headers={"X-API-KEY": self.FORC_API_KEY})
            if response.status_code == 401:
                return [response.json()]
            else:
                return response.json()
        except Timeout as e:
            self.logger.info(msg="get_templates timed out. {0}".format(e))

    def get_allowed_templates(self):
        get_url = "{0}templates/".format(self.RE_BACKEND_URL)
        try:
            response = req.get(get_url, timeout=(30, 30), headers={"X-API-KEY": self.FORC_API_KEY})
            if response.status_code == 401:
                return [response.json()]
            elif response.status_code == 200:
                templates = self.cross_check_templates(response.json())
                return templates
        except Timeout as e:
            self.logger.info(msg="create_backend timed out. {0}".format(e))

    def get_templates_by_template(self, template_name):
        get_url = "{0}/templates/{1}".format(self.RE_BACKEND_URL, template_name)
        try:
            response = req.get(get_url, timeout=(30, 30), headers={"X-API-KEY": self.FORC_API_KEY})
            if response.status_code == 401:
                return [response.json()]
            else:
                return response.json()
        except Timeout as e:
            self.logger.info(msg="get_templates_by_template timed out. {0}".format(e))

    def check_template(self, template_name, template_version):
        get_url = "{0}/templates/{1}/{2}".format(self.RE_BACKEND_URL, template_name,
                                                 template_version)
        try:
            response = req.get(get_url, timeout=(30, 30), headers={"X-API-KEY": self.FORC_API_KEY})
            if response.status_code == 401:
                return [response.json()]
            else:
                return response.json()
        except Timeout as e:
            self.logger.info(msg="check_template timed out. {0}".format(e))

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

    def get_volumes_by_ids(self, volume_ids):
        self.logger.info("Get Volumes {}".format(volume_ids))

        volumes = []
        for id in volume_ids:
            try:
                os_volume = self.conn.get_volume_by_id(id=id)
                thrift_volume = Volume(status=os_volume.status, id=os_volume.id,
                                       name=os_volume.name,
                                       description=os_volume.description,
                                       created_at=os_volume.created_at)
                volumes.append(thrift_volume)

            except Exception:
                self.logger.exception("Could not find volume {}".format(id))


        return volumes

    def get_volume(self, volume_id):
        self.logger.info("Get Volume {}".format(volume_id))
        try:

            os_volume = self.conn.get_volume_by_id(id=volume_id)

            thrift_volume = Volume(status=os_volume.status, id=os_volume.id, name=os_volume.name,
                                   description=os_volume.description, created_at=os_volume.created_at)
            return thrift_volume
        except Exception:
            self.logger.exception("Could not find volume {}".format(id))
            return  Volume(status="NOT FOUND")

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
                            self.logger.exception(
                                "Could not attach volume {} to instance {}".format(volume_id,
                                                                                   openstack_id))

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
            elif serv["status"] == self.ERROR:
                server = self.get_server(openstack_id)
                server.status = self.ERROR
                return server
            else:
                server = self.get_server(openstack_id)
                server.status = self.BUILD
                return server
        except Exception as e:
            self.logger.exception("Check Status VM {0} error: {1}".format(openstack_id, e))
            return None

    def openstack_server_to_thrift_server(self, server):
        self.logger.info("Convert server {} to thrift server".format(server))
        fixed_ip = None
        floating_ip = None
        diskspace = 0

        if server["os-extended-volumes:volumes_attached"]:
            volume_id = server["os-extended-volumes:volumes_attached"][0]["id"]
            try:
                diskspace = self.conn.block_storage.get_volume(volume_id).to_dict()["size"]
            except Exception as e:
                self.logger.exception("Could not found volume {}: {}".format(volume_id, e))

        if server["OS-SRV-USG:launched_at"]:
            dt = datetime.datetime.strptime(
                server["OS-SRV-USG:launched_at"][:-7], "%Y-%m-%dT%H:%M:%S"
            )
            timestamp = time.mktime(dt.timetuple())
        else:
            timestamp = None
        flav = self.openstack_flav_to_thrift_flav(server["flavor"])

        try:
            img = self.get_Image_with_Tag(server["image"]["id"])
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
            flav=flav,
            img=img,
            status=server["status"],
            metadata=server["metadata"],
            project_id=server["project_id"],
            keyname=server["key_name"],
            openstack_id=server["id"],
            name=server["name"],
            created_at=str(timestamp),
            fixed_ip=fixed_ip,
            floating_ip=floating_ip,
            diskspace=diskspace,
        )
        return server

    def get_servers(self):
        self.logger.info("Get all servers")
        servers = self.conn.list_servers()
        self.logger.info("Found {} servers".format(len(servers)))
        server_list = []
        for server in servers:
            try:
                thrift_server = self.openstack_server_to_thrift_server(server)
                server_list.append(thrift_server)

            except Exception as e:
                self.logger.exception("Could not transform to thrift_server: {}".format(e))
        self.logger.info("Converted {} servers to thrift_server objects".format(len(server_list)))
        # self.logger.info(server_list)
        return server_list

    def add_udp_security_group(self, server_id):
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
        server = self.conn.get_server(name_or_id=server_id)
        if server is None:
            self.logger.exception("Instance {0} not found".format(server_id))
            raise serverNotFoundException
        sec = self.conn.get_security_group(name_or_id=server.name + "_udp")
        if sec:
            self.logger.info(
                "Security group with name {} already exists.".format(server.name + "_udp"))
            self.conn.compute.add_security_group_to_server(
                server=server_id, security_group=sec
            )

            return True

        ip_base = \
            list(self.conn.compute.server_ips(server=server_id))[0].to_dict()['address'].split(".")[
                -1]
        x = int(ip_base)
        udp_port_start = eval(self.UDP_PORT_CALCULATION)

        security_group = self.create_security_group(
            name=server.name + "_udp",
            udp_port_start=udp_port_start,
            udp=True,
            ssh=False,
            https=False,
            http=False, description="UDP"
        )
        self.logger.info(security_group)
        self.logger.info("Add security group {} to server {} ".format(security_group.id, server_id))
        self.conn.compute.add_security_group_to_server(
            server=server_id, security_group=security_group
        )

        return True

    def get_servers_by_bibigrid_id(self, bibigrid_id):
        filters = {"bibigrid_id": bibigrid_id, "name": bibigrid_id}
        servers = self.conn.list_servers(filters=filters)
        thrift_servers = []
        for server in servers:
            thrift_servers.append(self.openstack_server_to_thrift_server(server))
        return thrift_servers

    def get_vm_ports(self, openstack_id):
        """
               Get Ports of the sever.

               :param openstack_id: Id of the server
               :return: {'PORT': port, 'UDP':start_port}
               """
        self.logger.info("Get IP and PORT for server {0}".format(openstack_id))
        server = self.get_server(openstack_id)
        server_base = server.fixed_ip.split(".")[-1]
        x = int(server_base)
        port = eval(self.SSH_PORT_CALCULATION)
        udp_port_start = eval(self.UDP_PORT_CALCULATION)
        return {"port": str(port), "udp": str(udp_port_start)}


    def get_cluster_status(self,cluster_id):
        headers = {"content-Type": "application/json"}
        body = {"mode": "openstack"}
        request_url = self.BIBIGRID_URL + 'info/' + cluster_id
        response = req.get(url=request_url, json=body, headers=headers,
                           verify=False)
        return response.json()

    def get_cluster_info(self, cluster_id):
        headers = {"content-Type": "application/json"}
        body = {"mode": "openstack"}
        request_url = self.BIBIGRID_URL + 'list'
        self.logger.info(request_url)

        response = req.get(url=request_url, json=body, headers=headers,
                           verify=False)
        self.logger.info(response.json())
        infos = response.json()["info"]
        for info in infos:
            self.logger.info(cluster_id)
            self.logger.info(info)
            self.logger.info(info["cluster-id"])
            self.logger.info(cluster_id == info["cluster-id"])
            if info["cluster-id"] == cluster_id:
                cluster_info = ClusterInfo(launch_date=info["launch date"],
                                           group_id=info["group-id"],
                                           network_id=info["network-id"],
                                           public_ip=info["public-ip"],
                                           subnet_id=info["subnet-id"],
                                           user=info["user"],
                                           inst_counter=info["# inst"],
                                           cluster_id=info["cluster-id"],
                                           key_name=info["key name"])
                self.logger.info("CLuster info : {}".format(cluster_info))
                return cluster_info

        return None

    def get_calculation_formulars(self):
        return {"ssh_port_calculation": self.SSH_FORMULAR,
                "udp_port_calculation": self.UDP_FORMULAR}

    def get_gateway_ip(self):
        return {"gateway_ip": self.GATEWAY_IP}

    def start_cluster(self, public_key, master_instance, worker_instances, user):
        master_instance = master_instance.__dict__
        del master_instance['count']
        wI = []
        for wk in worker_instances:
            self.logger.info(wk)
            wI.append(wk.__dict__)
        headers = {"content-Type": "application/json"}
        body = {"mode": "openstack", "subnet": self.SUB_NETWORK, "user": user, "sshUser": "ubuntu",
                "availabilityZone": self.AVAIALABILITY_ZONE, "masterInstance": master_instance,
                "workerInstances": wI}
        request_url = self.BIBIGRID_URL + 'create'
        response = req.post(url=request_url, json=body, headers=headers,
                                verify=False)
        self.logger.info(response.json())
        return response.json()


    def terminate_cluster(self, cluster_id):
        response = req.delete(url="{}terminate/{}".format(self.BIBIGRID_URL, cluster_id))
        self.logger.info(response.json())
        return response.json()

    def create_snapshot(self, openstack_id, name, elixir_id, base_tags, description):
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

                for tag in base_tags:
                    self.conn.image.add_tag(
                        image=snapshot_id, tag=tag
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
            server = self.conn.get_server(openstack_id)
            if server is None:
                self.logger.exception("Instance {0} not found".format(openstack_id))
                return True
            security_groups = self.conn.list_server_security_groups(server=server)
            self.logger.info(security_groups)
            security_groups = [sec for sec in security_groups if
                               sec.name != self.DEFAULT_SECURITY_GROUP]
            if security_groups is not None:
                for sg in security_groups:
                    self.logger.info("Delete security group {0}".format(sg.name))
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
            self, name, udp_port_start=None, ssh=True, http=False, https=False, udp=False,
            description=None, resenv=[]
    ):
        self.logger.info("Create new security group {}".format(name))
        sec = self.conn.get_security_group(name_or_id=name)
        if sec:
            self.logger.info("Security group with name {} already exists.".format(name))
            return sec
        new_security_group = self.conn.create_security_group(name=name, description=description)
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

        if THEIA in resenv:
            self.logger.info("Add theia rule to security group {}".format(name))

            self.conn.network.create_security_group_rule(
                direction="ingress",
                protocol="tcp",
                port_range_max=8080,
                port_range_min=8080,
                security_group_id=new_security_group["id"],
            )
        if GUACAMOLE in resenv:
            self.logger.info("Add guacamole rule to security group {}".format(name))

            self.conn.network.create_security_group_rule(
                direction="ingress",
                protocol="tcp",
                port_range_max=8080,
                port_range_min=8080,
                security_group_id=new_security_group["id"],
            )
        if RSTUDIO in resenv:
            self.logger.info("Add rstudio rule to security group {}".format(name))

            self.conn.network.create_security_group_rule(
                direction="ingress",
                protocol="tcp",
                port_range_max=8787,
                port_range_min=8787,
                security_group_id=new_security_group["id"],
            )
        if JUPYTERNOTEBOOK in resenv:
            self.logger.info("Add jupyternotebook rule to security group {}".format(name))

            self.conn.network.create_security_group_rule(
                direction="ingress",
                protocol="tcp",
                port_range_max=8080,
                port_range_min=8080,
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
