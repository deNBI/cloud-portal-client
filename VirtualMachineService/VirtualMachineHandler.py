"""
This Module implements an VirtualMachineHandler.

Which can be used for the PortalClient.
"""
import sys
from uuid import uuid4

try:
    from VirtualMachineService import Iface
    from ttypes import serverNotFoundException
    from ttypes import imageNotFoundException
    from ttypes import networkNotFoundException
    from ttypes import authenticationException
    from ttypes import otherException
    from ttypes import flavorNotFoundException
    from ttypes import ressourceException
    from ttypes import conflictException
    from ttypes import Flavor, Image, VM, PlaybookResult, Backend, ClusterInfo, Volume
    from constants import VERSION
    from ancon.Playbook import (
        Playbook,
        ALL_TEMPLATES,
    )

except Exception:
    from .VirtualMachineService import Iface
    from .ttypes import serverNotFoundException
    from .ttypes import imageNotFoundException
    from .ttypes import networkNotFoundException
    from .ttypes import authenticationException
    from .ttypes import otherException
    from .ttypes import flavorNotFoundException
    from .ttypes import ressourceException
    from .ttypes import conflictException
    from .ttypes import Flavor, Image, VM, PlaybookResult, Backend, ClusterInfo, Volume
    from .constants import VERSION
    from .ancon.Playbook import (
        Playbook,
        ALL_TEMPLATES,
    )

import datetime
import json
import logging
import os
import parser
import socket
import time
import urllib
from contextlib import closing
from distutils.version import LooseVersion

import redis
import requests as req
import yaml
from deprecated import deprecated
from keystoneauth1 import session
from keystoneauth1.identity import v3
from keystoneclient.v3 import client
from openstack import connection
from openstack.exceptions import ConflictException
from oslo_utils import encodeutils
from requests.exceptions import Timeout

active_playbooks = dict()

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
fh = logging.FileHandler("log/portal_client_debug.log")
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(funcName)s  - %(levelname)s - %(message)s"
)
fh.setFormatter(formatter)
ch.setFormatter(formatter)
LOG.addHandler(fh)
LOG.addHandler(ch)
PLAYBOOKS_DIR = "/code/VirtualMachineService/ancon/playbooks/"

PORT = "port"
SECURITYGROUP_NAME = "securitygroup_name"
SECURITYGROUP_DESCRIPTION = "securitygroup_description"
SECURITYGROUP_SSH = "securitygroup_ssh"
DIRECTION = "direction"
PROTOCOL = "protocol"
TEMPLATE_NAME = "template_name"
INFORMATION_FOR_DISPLAY = "information_for_display"
FORC_VERSIONS = "forc_versions"


class VirtualMachineHandler(Iface):
    """Handler which the PortalClient uses."""

    global active_playbooks
    API_TOKEN = None
    API_TOKEN_BUFFER = 15
    BUILD = "BUILD"
    ACTIVE = "ACTIVE"
    ERROR = "ERROR"
    SHUTOFF = "SHUTOFF"
    NOT_FOUND = "NOT_FOUND"
    PREPARE_PLAYBOOK_BUILD = "PREPARE_PLAYBOOK_BUILD"
    BUILD_PLAYBOOK = "BUILD_PLAYBOOK"
    PLAYBOOK_FAILED = "PLAYBOOK_FAILED"
    DEFAULT_SECURITY_GROUP = "defaultSimpleVM"
    DEFAULT_SECURITY_GROUPS = [DEFAULT_SECURITY_GROUP]
    ALL_TEMPLATES = ALL_TEMPLATES
    loaded_resenv_metadata = {}

    def keyboard_interrupt_handler_playbooks(self):
        global active_playbooks
        for k, v in active_playbooks.items():
            LOG.info("Clearing traces of Playbook-VM for (openstack_id): {0}".format(k))
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
                project_domain_id=self.PROJECT_DOMAIN_ID,
            )
            conn.authorize()
        except Exception as e:
            LOG.exception("Client failed authentication at Openstack : {0}", e)
            raise authenticationException(
                Reason="Client failed authentication at Openstack"
            )

        LOG.info("Connected to Openstack")
        return conn

    def __init__(self, config):
        """
        Initialize the handler.

        Read all config variables and creates a connection to OpenStack.
        """

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
            self.PRODUCTION = cfg["openstack_connection"]["production"]
            self.CLOUD_SITE = cfg["cloud_site"]
            # connection to redis. Uses a pool with 10 connections.
            self.REDIS_HOST = cfg["redis"]["host"]
            self.REDIS_PORT = cfg["redis"]["port"]
            self.REDIS_PASSWORD = cfg["redis"].get("password", None)
            LOG.info(f"Connecting to Redis at {self.REDIS_HOST}:{self.REDIS_PORT}..")
            self.pool = redis.ConnectionPool(
                host=self.REDIS_HOST, port=self.REDIS_PORT, password=self.REDIS_PASSWORD
            )

            self.redis = redis.Redis(connection_pool=self.pool, charset="utf-8")
            try:
                self.redis.ping()
                LOG.info("Connected to Redis!")
            except redis.ConnectionError:
                LOG.exception("Could not connect to Redis!")
                sys.exit(1)

            # try to initialize forc connection
            try:
                self.SUB_NETWORK = cfg["bibigrid"]["sub_network"]
                self.BIBIGRID_MODES = cfg["bibigrid"]["bibigrid_modes"]
                self.BIBIGRID_HOST = cfg["bibigrid"]["host"]
                self.BIBIGRID_PORT = cfg["bibigrid"]["port"]
                if cfg["bibigrid"].get("https", False):
                    self.BIBIGRID_URL = (
                        f"https://{self.BIBIGRID_HOST}:{self.BIBIGRID_PORT}/bibigrid/"
                    )
                    self.BIBIGIRD_EP = (
                        f"https://{self.BIBIGRID_HOST}:{self.BIBIGRID_PORT}"
                    )
                else:
                    self.BIBIGRID_URL = (
                        f"http://{self.BIBIGRID_HOST}:{self.BIBIGRID_PORT}/bibigrid/"
                    )
                    self.BIBIGIRD_EP = (
                        f"http://{self.BIBIGRID_HOST}:{self.BIBIGRID_PORT}"
                    )

                LOG.info(msg="Bibigrd url loaded: {0}".format(self.BIBIGRID_URL))
            except Exception as e:
                LOG.exception(e)
                LOG.info("Bibigrid not loaded.")
                self.BIBIGRID_URL = None
                self.SUB_NETWORK = None

            try:
                self.RE_BACKEND_URL = cfg["forc"]["forc_url"]
                self.FORC_API_KEY = cfg["forc"]["forc_api_key"]
                self.FORC_ALLOWED = {}
                self.GITHUB_PLAYBOOKS_REPO = cfg["forc"]["github_playbooks_repo"]
                if (
                    not self.RE_BACKEND_URL
                    or not self.FORC_API_KEY
                    or not self.GITHUB_PLAYBOOKS_REPO
                ):
                    raise ValueError
                LOG.info(msg="Forc-Backend url loaded: {0}".format(self.RE_BACKEND_URL))
            except ValueError as ve:
                LOG.exception(ve)
                LOG.info(
                    "Forc-Backend not loaded as one of the configurations was empty."
                )
                self.RE_BACKEND_URL = None
                self.FORC_API_KEY = None
                self.FORC_ALLOWED = None
                self.GITHUB_PLAYBOOKS_REPO = None
            except Exception as e:
                LOG.exception(e)
                LOG.info("Forc-Backend not loaded.")
                self.RE_BACKEND_URL = None
                self.FORC_API_KEY = None
                self.FORC_ALLOWED = None
                self.GITHUB_PLAYBOOKS_REPO = None
            if self.USE_GATEWAY:
                self.GATEWAY_IP = cfg["openstack_connection"]["gateway_ip"]
                self.SSH_FORMULAR = cfg["openstack_connection"][
                    "ssh_port_calc_formular"
                ]
                self.UDP_FORMULAR = cfg["openstack_connection"][
                    "udp_port_calc_formular"
                ]
                self.SSH_PORT_CALCULATION = parser.expr(self.SSH_FORMULAR).compile()
                self.UDP_PORT_CALCULATION = parser.expr(self.UDP_FORMULAR).compile()
                LOG.info("Gateway IP is {}".format(self.GATEWAY_IP))
        self.update_playbooks()
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
                    return None

                keystone = client.Client(session=sess)
                user = findUser(keystone, user)
                keystone.users.update(user, password=password)
                return password
            except Exception as e:
                LOG.exception(
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
        LOG.info("Get Flavors")
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
                    ephemeral_disk=flav["ephemeral"],
                )
                LOG.info(flavor)
                flavors.append(flavor)
            return flavors
        except Exception as e:
            LOG.exception("Get Flavors Error: {0}".format(e))
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
        LOG.info(
            "Compare Version : Server Version = {0} "
            "|| Client Version = {1}".format(VERSION, version)
        )
        try:
            if version == VERSION:
                return True
            else:
                return False
        except Exception as e:
            LOG.exception("Compare Version Error: {0}".format(e))
            return False

    def get_client_version(self):
        """
        Get client version.

        :return: Version of the client.
        """
        # LOG.info("Get Version of Client: {}".format(VERSION))
        return str(VERSION)

    def get_Images(self):
        """
        Get Images.

        :return: List of image instances.
        """
        LOG.info("Get Images")
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
                LOG.info(set(self.ALL_TEMPLATES).intersection(tags))
                if len(
                    set(self.ALL_TEMPLATES).intersection(tags)
                ) > 0 and not self.cross_check_forc_image(tags):
                    LOG.info("Resenv check: Skipping {0}.".format(img["name"]))
                    continue
                image_type = img.get("image_type", "image")
                if description is None:
                    LOG.warning("No Description and  for " + img["name"])

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
                    is_snapshot=image_type == "snapshot",
                )
                LOG.info(image)

                images.append(image)

            return images
        except Exception as e:
            LOG.exception("Get Images Error: {0}".format(e))
            return ()

    def prepare_image(self, img):
        try:
            metadata = img["metadata"]
            description = metadata.get("description")
            tags = img.get("tags")
            LOG.info(set(self.ALL_TEMPLATES).intersection(tags))
            if len(
                set(self.ALL_TEMPLATES).intersection(tags)
            ) > 0 and not self.cross_check_forc_image(tags):
                LOG.info("Resenv check: Skipping {0}.".format(img["name"]))
                return None
            image_type = img.get("image_type", "image")
            if description is None:
                LOG.warning("No Description for " + img["name"])

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
                is_snapshot=image_type == "snapshot",
            )
            LOG.info(image)
            return image
        except Exception as e:
            LOG.exception("Prepare image Error: {0}".format(e))
            return None

    def get_public_Images(self):
        """
        Get Images.

        :return: List of image instances.
        """
        LOG.info("Get public Images")
        images = list()
        try:
            for img in filter(
                lambda x: "tags" in x
                and len(x["tags"]) > 0
                and x["status"] == "active"
                and x["visibility"] == "public",
                self.conn.list_images(),
            ):
                image = self.prepare_image(img)
                if image is None:
                    continue
                else:
                    images.append(image)
            return images
        except Exception as e:
            LOG.exception("Get Images Error: {0}".format(e))
            return ()

    def get_private_Images(self):
        """
        Get Images.

        :return: List of image instances.
        """
        LOG.info("Get private Images")
        images = list()
        try:
            for img in filter(
                lambda x: "tags" in x
                and len(x["tags"]) > 0
                and x["status"] == "active"
                and x["visibility"] == "private",
                self.conn.list_images(),
            ):
                image = self.prepare_image(img)
                if image is None:
                    continue
                else:
                    images.append(image)
            return images
        except Exception as e:
            LOG.exception("Get Images Error: {0}".format(e))
            return ()

    def get_Image_with_Tag(self, id):
        """
        Get Image with Tags.

        :param id: Id of the image
        :return: Image instance
        """
        LOG.info("Get Image {0} with tags".format(id))
        try:
            img = self.conn.get_image(name_or_id=id)
            if not img:
                return None
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
            LOG.exception("Get Image {0} with Tag Error: {1}".format(id, e))
            return None

    def get_Images_by_filter(self, filter_list):
        """
        Get filtered Images.

        :return: List of image instances.
        """
        LOG.info("Get filtered Images: {0}".format(filter_list))
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
                    LOG.info(modes)
                    if "resenv" in tags and not self.cross_check_forc_image(tags):
                        continue
                metadata = img["metadata"]
                description = metadata.get("description")
                image_type = img.get("image_type", "image")
                if description is None:
                    LOG.warning("No Description for {0}".format(img["name"]))

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
                    is_snapshot=image_type == "snapshot",
                )
                LOG.info(image)

                images.append(image)

            return images
        except Exception as e:
            LOG.exception("Get Images Error: {0}".format(e))
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
                LOG.info("Create Keypair {0}".format(keyname))

                keypair = self.conn.compute.create_keypair(
                    name=keyname, public_key=public_key
                )
                return keypair
            elif keypair.public_key != public_key:
                LOG.info("Key has changed. Replace old Key")
                self.conn.compute.delete_keypair(keypair)
                keypair = self.conn.compute.create_keypair(
                    name=keyname, public_key=public_key
                )
                return keypair
            return keypair
        except Exception as e:
            LOG.exception("Import Keypair {0} error:{1}".format(keyname, e))
            return None

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
            LOG.exception(e)
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
        LOG.info("Get Server {0}".format(openstack_id))
        try:
            server = self.conn.compute.get_server(openstack_id)
        except Exception as e:
            LOG.exception("No Server found {0} | Error {1}".format(openstack_id, e))
            return VM(status=self.NOT_FOUND)

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
            LOG.exception(e)
            img = None
        for values in server.addresses.values():
            for address in values:

                if address["OS-EXT-IPS:type"] == "floating":
                    floating_ip = address["addr"]
                elif address["OS-EXT-IPS:type"] == "fixed":
                    fixed_ip = address["addr"]
        task = serv["task_state"]
        if task:
            status = task.upper().replace("-", "_")
            LOG.info(f"{openstack_id} Task: {task}")

        else:
            status = serv["status"]

        if floating_ip:
            server = VM(
                flav=flav,
                img=img,
                status=status,
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
                status=status,
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
            LOG.info("Get server {}".format(id))
            try:
                server = self.conn.get_server_by_id(id)
                servers.append(server)
            except Exception as e:
                LOG.exception("Requested VM {} not found!\n {}".format(id, e))
        server_list = []
        for server in servers:
            if server:
                server_list.append(self.openstack_server_to_thrift_server(server))
        return server_list

    def check_server_task_state(self, openstack_id):
        LOG.info("Checking Task State: {}".format(openstack_id))
        server = self.conn.get_server_by_id(openstack_id)
        LOG.info(server)
        if not server:
            return "No server found"
        task_state = server.get("task_state", None)
        LOG.info("Task State: {}".format(task_state))
        if task_state:
            return task_state
        else:
            return "No active task"

    def get_image(self, image):
        image = self.conn.compute.find_image(image)
        if image is None:
            LOG.exception("Image {0} not found!".format(image))
            raise imageNotFoundException(Reason=("Image {0} not found".format(image)))
        return image

    def get_flavor(self, flavor):
        flavor = self.conn.compute.find_flavor(flavor)
        if flavor is None:
            LOG.exception("Flavor {0} not found!".format(flavor))
            raise flavorNotFoundException(Reason="Flavor {0} not found!".format(flavor))
        return flavor

    def get_network(self):
        network = self.conn.network.find_network(self.NETWORK)
        if network is None:
            LOG.exception("Network {0} not found!".format(network))
            raise networkNotFoundException(
                Reason="Network {0} not found!".format(network)
            )
        return network

    def create_add_keys_script(self, keys):
        LOG.info(f"create add key script")
        fileDir = os.path.dirname(os.path.abspath(__file__))
        key_script = os.path.join(fileDir, "scripts/bash/add_keys_to_authorized.sh")
        bash_keys_array = "("
        for key in keys:
            bash_keys_array += f'"{key}" '
        bash_keys_array += ")"

        with open(key_script, "r") as file:
            text = file.read()
            text = text.replace("KEYS_TO_ADD", bash_keys_array)
            text = encodeutils.safe_encode(text.encode("utf-8"))
        key_script = text
        return key_script

    def create_mount_init_script(
        self, volume_ids_path_new=None, volume_ids_path_attach=None
    ):
        LOG.info("create init script for volume ids:{}".format(volume_ids_path_new))
        if not volume_ids_path_new and not volume_ids_path_attach:
            return None

        fileDir = os.path.dirname(os.path.abspath(__file__))
        mount_script = os.path.join(fileDir, "scripts/bash/mount.sh")

        if volume_ids_path_new:
            volume_ids_new = [vol["openstack_id"] for vol in volume_ids_path_new]
            paths_new = [vol["path"] for vol in volume_ids_path_new]
        else:
            volume_ids_new = []
            paths_new = []

        if volume_ids_path_attach:
            volume_ids_attach = [vol["openstack_id"] for vol in volume_ids_path_attach]
            paths_attach = [vol["path"] for vol in volume_ids_path_attach]
        else:
            volume_ids_attach = []
            paths_attach = []

        bash_volume_path_new_array_string = "("
        for path in paths_new:
            bash_volume_path_new_array_string += path + " "
        bash_volume_path_new_array_string += ")"

        bash_volume_path_attach_array_string = "("
        for path in paths_attach:
            bash_volume_path_attach_array_string += path + " "
        bash_volume_path_attach_array_string += ")"

        bash_volume_id_new_array_string = "("
        for volume_id in volume_ids_new:
            bash_volume_id_new_array_string += "virtio-" + volume_id[0:20] + " "
        bash_volume_id_new_array_string += ")"

        bash_volume_id_attach_array_string = "("
        for volume_id in volume_ids_attach:
            bash_volume_id_attach_array_string += "virtio-" + volume_id[0:20] + " "
        bash_volume_id_attach_array_string += ")"

        with open(mount_script, "r") as file:
            text = file.read()
            text = text.replace("VOLUME_IDS_NEW", bash_volume_id_new_array_string)
            text = text.replace("VOLUME_PATHS_NEW", bash_volume_path_new_array_string)
            text = text.replace("VOLUME_IDS_ATTACH", bash_volume_id_attach_array_string)
            text = text.replace(
                "VOLUME_PATHS_ATTACH", bash_volume_path_attach_array_string
            )
            text = encodeutils.safe_encode(text.encode("utf-8"))
        init_script = text
        LOG.info(init_script)
        return init_script

    def get_api_token(self):
        self.get_or_refresh_token()
        return str(self.API_TOKEN["token"])

    def get_or_refresh_token(self):
        LOG.info("Get API Token")
        if not self.API_TOKEN:
            LOG.info("Create a new API Token")
            auth_url = self.conn.endpoint_for("identity")
            LOG.info(auth_url)
            auth = {
                "auth": {
                    "identity": {
                        "methods": ["password"],
                        "password": {
                            "user": {
                                "name": self.USERNAME,
                                "domain": {"name": self.USER_DOMAIN_NAME},
                                "password": self.PASSWORD,
                            }
                        },
                    },
                    "scope": {
                        "project": {
                            "domain": {"id": "default"},
                            "name": self.PROJECT_NAME,
                        }
                    },
                }
            }
            res = req.post(url=auth_url + "/auth/tokens?nocatalog", json=auth)

            expires_at = datetime.datetime.strptime(
                res.json()["token"]["expires_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )

            self.API_TOKEN = {
                "token": res.headers["X-Subject-Token"],
                "expires_at": expires_at,
            }
            LOG.info("New Token: {}".format(self.API_TOKEN))
        else:
            LOG.info("Check existing token")
            now = datetime.datetime.now()
            # some buffer
            now = now - datetime.timedelta(minutes=self.API_TOKEN_BUFFER)
            api_token_expires_at = self.API_TOKEN["expires_at"]
            if now.time() > api_token_expires_at.time():
                expired_since = api_token_expires_at - now
                LOG.info(
                    "Old token is expired since {} minutes!".format(
                        expired_since.seconds // 60
                    )
                )
                self.API_TOKEN = None
                self.get_api_token()
            else:
                LOG.info("Token still valid!")

    def resize_volume(self, volume_id, size):
        try:
            self.conn.block_storage.extend_volume(volume_id, size)
        except Exception as e:
            LOG.exception(e)
            return 1
        return 0

    def create_volume(self, volume_name, volume_storage, metadata):
        """
        Create volume.
        :param volume_name: Name of volume
        :param volume_storage: volume_storage in GB for new volume
        :return: Id of new volume
        """
        LOG.info("Creating volume with {0} GB diskspace".format(volume_storage))

        try:
            volume = self.conn.block_storage.create_volume(
                name=volume_name, size=volume_storage, metadata=metadata
            )
            LOG.info(volume)
            return {"volume_id": volume["id"]}
        except Exception as e:
            LOG.exception(
                "Trying to create volume with {0} GB  error : {1}".format(
                    volume_storage, e
                ),
                exc_info=True,
            )

            raise ressourceException(Reason=str(e))

    def volume_ids(
        self,
        flavor,
        image,
        public_key,
        servername,
        metadata,
        https,
        http,
        resenv,
        volume_ids_path_new,
        volume_ids_path_attach,
    ):
        image = self.get_image(image=image)
        flavor = self.get_flavor(flavor=flavor)
        network = self.get_network()
        key_name = f"{metadata.get('elixir_id')[:-18]}{str(uuid4())[0:5]}"
        public_key = urllib.parse.unquote(public_key)
        key_pair = self.import_keypair(key_name, public_key)
        init_script = self.create_mount_init_script(
            volume_ids_path_new=volume_ids_path_new,
            volume_ids_path_attach=volume_ids_path_attach,
        )
        custom_security_groups = self.prepare_security_groups_new_server(
            resenv=resenv, servername=servername, http=http, https=https
        )
        try:

            server = self.conn.create_server(
                name=servername,
                image=image.id,
                flavor=flavor.id,
                network=[network.id],
                key_name=key_pair.name,
                meta=metadata,
                userdata=init_script,
                availability_zone=self.AVAIALABILITY_ZONE,
                security_groups=self.DEFAULT_SECURITY_GROUPS + custom_security_groups,
            )
            openstack_id = server["id"]
            self.delete_keypair(key_name)

            return {"openstack_id": openstack_id}

        except Exception as e:
            self.delete_keypair(key_name)
            for security_group in custom_security_groups:
                self.conn.network.delete_security_group(security_group)
            LOG.exception("Start Server {1} error:{0}".format(e, servername))
            return {}

    def prepare_security_groups_new_server(self, resenv, servername, http, https):
        custom_security_groups = []

        custom_security_groups.append(
            self.create_security_group(
                name=servername + "_ssh", description="Only SSH"
            ).name
        )

        if http or https:
            custom_security_groups.append(
                self.create_security_group(
                    name=servername + "_https",
                    http=http,
                    https=https,
                    description="Http/Https",
                ).name
            )

        for research_enviroment in resenv:
            if research_enviroment in self.loaded_resenv_metadata:
                resenv_metadata = self.loaded_resenv_metadata[research_enviroment]
                custom_security_groups.append(
                    self.create_security_group(
                        name=servername + resenv_metadata.security_group_name,
                        resenv=resenv,
                        description=resenv_metadata.security_group_description,
                        ssh=resenv_metadata.security_group_ssh,
                    ).name
                )
            elif research_enviroment != "user_key_url":
                LOG.error(
                    "Failure to load metadata  of reasearch enviroment: "
                    + research_enviroment
                )

        return custom_security_groups

    def start_server_without_playbook(
        self,
        flavor,
        image,
        public_key,
        servername,
        metadata,
        https,
        http,
        resenv,
        volume_ids_path_new=None,
        volume_ids_path_attach=None,
        additional_keys=None,
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
        LOG.info("Start Server {0}".format(servername))
        custom_security_groups = self.prepare_security_groups_new_server(
            resenv=resenv, servername=servername, http=http, https=https
        )
        key_name = None
        try:
            image = self.get_image(image=image)
            flavor = self.get_flavor(flavor=flavor)
            network = self.get_network()
            key_name = f"{metadata.get('elixir_id')[:-18]}{str(uuid4())[0:5]}"

            public_key = urllib.parse.unquote(public_key)
            key_pair = self.import_keypair(key_name, public_key)
            volume_ids = []
            volumes = []

            if volume_ids_path_new:
                volume_ids.extend([vol["openstack_id"] for vol in volume_ids_path_new])
            if volume_ids_path_attach:
                volume_ids.extend(
                    [vol["openstack_id"] for vol in volume_ids_path_attach]
                )
            for id in volume_ids:
                volumes.append(self.conn.get_volume_by_id(id=id))
            init_script = self.create_mount_init_script(
                volume_ids_path_new=volume_ids_path_new,
                volume_ids_path_attach=volume_ids_path_attach,
            )
            if additional_keys:
                if init_script:
                    add_key_script = self.create_add_keys_script(keys=additional_keys)
                    init_script = (
                        add_key_script
                        + encodeutils.safe_encode("\n".encode("utf-8"))
                        + init_script
                    )

                else:
                    init_script = self.create_add_keys_script(keys=additional_keys)

            server = self.conn.create_server(
                name=servername,
                image=image.id,
                flavor=flavor.id,
                network=[network.id],
                key_name=key_pair.name,
                meta=metadata,
                volumes=volumes,
                userdata=init_script,
                availability_zone=self.AVAIALABILITY_ZONE,
                security_groups=self.DEFAULT_SECURITY_GROUPS + custom_security_groups,
            )

            openstack_id = server["id"]
            self.delete_keypair(key_name)

            return {"openstack_id": openstack_id}
        except Exception as e:
            if key_name:
                self.delete_keypair(key_name)

            for security_group in custom_security_groups:
                self.conn.network.delete_security_group(security_group)
            LOG.exception("Start Server {1} error:{0}".format(e, servername))
            return {}

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
        resenv,
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
        LOG.info("Start Server {0}".format(servername))
        custom_security_groups = self.prepare_security_groups_new_server(
            resenv=resenv, servername=servername, http=http, https=https
        )
        key_name = None
        try:
            image = self.get_image(image=image)
            flavor = self.get_flavor(flavor=flavor)
            network = self.get_network()
            key_name = f"{metadata.get('elixir_id')[:-18]}{str(uuid4())[0:5]}"
            public_key = urllib.parse.unquote(public_key)
            key_pair = self.import_keypair(key_name, public_key)

            server = self.conn.create_server(
                name=servername,
                image=image.id,
                flavor=flavor.id,
                network=[network.id],
                key_name=key_pair.name,
                meta=metadata,
                availability_zone=self.AVAIALABILITY_ZONE,
                security_groups=self.DEFAULT_SECURITY_GROUPS + custom_security_groups,
            )

            openstack_id = server["id"]
            self.delete_keypair(key_name)

            return {"openstack_id": openstack_id}
        except Exception as e:
            if key_name:
                self.delete_keypair(key_name)
            for security_group in custom_security_groups:
                self.conn.network.delete_security_group(security_group)
            LOG.exception("Start Server {1} error:{0}".format(e, servername))
            return {}

    def start_server_with_custom_key(
        self,
        flavor,
        image,
        servername,
        metadata,
        http,
        https,
        resenv,
        volume_ids_path_new=None,
        volume_ids_path_attach=None,
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
        LOG.info("Start Server {} with custom key".format(servername))
        custom_security_groups = self.prepare_security_groups_new_server(
            resenv=resenv, servername=servername, http=http, https=https
        )
        try:
            image = self.get_image(image=image)
            flavor = self.get_flavor(flavor=flavor)
            network = self.get_network()
            key_creation = self.conn.create_keypair(name=servername)
            init_script = self.create_mount_init_script(
                volume_ids_path_new=volume_ids_path_new,
                volume_ids_path_attach=volume_ids_path_attach,
            )
            volume_ids = []
            volumes = []

            if volume_ids_path_new:
                volume_ids.extend([vol["openstack_id"] for vol in volume_ids_path_new])
            if volume_ids_path_attach:
                volume_ids.extend(
                    [vol["openstack_id"] for vol in volume_ids_path_attach]
                )
            for id in volume_ids:
                volumes.append(self.conn.get_volume_by_id(id=id))
            LOG.info(volumes)

            try:
                private_key = key_creation["private_key"]
            except Exception:
                private_key = key_creation.__dict__["private_key"]

            server = self.conn.create_server(
                name=servername,
                image=image.id,
                flavor=flavor.id,
                network=[network.id],
                key_name=servername,
                userdata=init_script,
                volumes=volumes,
                meta=metadata,
                availability_zone=self.AVAIALABILITY_ZONE,
                security_groups=self.DEFAULT_SECURITY_GROUPS + custom_security_groups,
            )

            openstack_id = server["id"]

            self.redis.hmset(
                openstack_id,
                dict(
                    key=private_key, name=servername, status=self.PREPARE_PLAYBOOK_BUILD
                ),
            )
            return {"openstackid": openstack_id, "private_key": private_key}
        except Exception as e:
            self.delete_keypair(key_name=servername)
            for security_group in custom_security_groups:
                self.conn.network.delete_security_group(security_group)
            LOG.exception("Start Server {1} error:{0}".format(e, servername))
            return {}

    def create_and_deploy_playbook(
        self, public_key, playbooks_information, openstack_id
    ):
        global active_playbooks
        LOG.info(msg="Starting Playbook for (openstack_id): {0}".format(openstack_id))
        port = self.get_vm_ports(openstack_id=openstack_id)
        key = self.redis.hget(openstack_id, "key").decode("utf-8")
        playbook = Playbook(
            ip=self.GATEWAY_IP,
            port=port["port"],
            playbooks_information=playbooks_information,
            osi_private_key=key,
            public_key=public_key,
            pool=self.pool,
            loaded_metadata_keys=list(self.loaded_resenv_metadata.keys()),
            cloud_site=self.CLOUD_SITE,
        )
        self.redis.hset(openstack_id, "status", self.BUILD_PLAYBOOK)
        playbook.run_it()
        active_playbooks[openstack_id] = playbook
        return 0

    def has_forc(self):
        return self.RE_BACKEND_URL is not None

    def get_forc_url(self):
        if self.RE_BACKEND_URL is None:
            return ""
        else:
            url = self.RE_BACKEND_URL.split(":5000", 1)[0]
            return "{0}/".format(url)

    def cross_check_forc_image(self, tags):
        get_url = "{0}templates/".format(self.RE_BACKEND_URL)
        try:
            response = req.get(
                get_url,
                timeout=(30, 30),
                headers={"X-API-KEY": self.FORC_API_KEY},
                verify=True,
            )
            if response.status_code != 200:
                return ()
            else:
                templates = response.json()
        except Exception as e:
            LOG.error("Could not get templates from FORC.\n {0}".format(e))
        cross_tags = list(set(self.ALL_TEMPLATES).intersection(tags))
        for template_dict in templates:
            if (
                template_dict["name"] in self.FORC_ALLOWED
                and template_dict["name"] in cross_tags
            ):
                if template_dict["version"] in self.FORC_ALLOWED[template_dict["name"]]:
                    return True
        return False

    def create_backend(self, elixir_id, user_key_url, template, upstream_url):
        template_version = self.get_template_version_for(template)
        if template_version is None:
            LOG.warning(
                "No suitable template version found for {0}. Aborting backend creation!".format(
                    template
                )
            )
            return {}
        try:
            post_url = "{0}backends/".format(self.RE_BACKEND_URL)
            backend_info = {
                "owner": elixir_id,
                "user_key_url": user_key_url,
                "template": template,
                "template_version": template_version,
                "upstream_url": upstream_url,
            }
        except Exception as e:
            LOG.exception(e)
            return {}
        try:
            response = req.post(
                post_url,
                json=backend_info,
                timeout=(30, 30),
                headers={"X-API-KEY": self.FORC_API_KEY},
                verify=True,
            )
            try:
                data = response.json()
            except Exception as e:
                LOG.exception(e)
                return {}
            LOG.info(f"Backend created {data}")
            return Backend(
                id=data["id"],
                owner=data["owner"],
                location_url=data["location_url"],
                template=data["template"],
                template_version=data["template_version"],
            )
        except Timeout as e:
            LOG.info(msg="create_backend timed out. {0}".format(e))
            return {}
        except Exception as e:
            LOG.exception(e)
            return {}

    def get_backends(self):
        get_url = "{0}/backends/".format(self.RE_BACKEND_URL)
        try:
            response = req.get(
                get_url,
                timeout=(30, 30),
                headers={"X-API-KEY": self.FORC_API_KEY},
                verify=True,
            )
            if response.status_code == 401:
                return [response.json()]
            else:
                backends = []
                for data in response.json():
                    backends.append(
                        Backend(
                            id=data["id"],
                            owner=data["owner"],
                            location_url=data["location_url"],
                            template=data["template"],
                            template_version=data["template_version"],
                        )
                    )
                return backends
        except Timeout as e:
            LOG.info(msg="create_backend timed out. {0}".format(e))
            return None

    def get_backends_by_owner(self, elixir_id):
        get_url = "{0}/backends/byOwner/{1}".format(self.RE_BACKEND_URL, elixir_id)
        try:
            response = req.get(
                get_url,
                timeout=(30, 30),
                headers={"X-API-KEY": self.FORC_API_KEY},
                verify=True,
            )
            if response.status_code == 401:
                return [response.json()]
            else:
                backends = []
                for data in response.json():
                    backends.append(
                        Backend(
                            id=data["id"],
                            owner=data["owner"],
                            location_url=data["location_url"],
                            template=data["template"],
                            template_version=data["template_version"],
                        )
                    )
                return backends
        except Timeout as e:
            LOG.info(msg="create_backend timed out. {0}".format(e))
            return None

    def get_backends_by_template(self, template):
        get_url = "{0}/backends/byTemplate/{1}".format(self.RE_BACKEND_URL, template)
        try:
            response = req.get(
                get_url,
                timeout=(30, 30),
                headers={"X-API-KEY": self.FORC_API_KEY},
                verify=True,
            )
            if response.status_code == 401:
                return [response.json()]
            else:
                backends = []
                for data in response.json():
                    backends.append(
                        Backend(
                            id=data["id"],
                            owner=data["owner"],
                            location_url=data["location_url"],
                            template=data["template"],
                            template_version=data["template_version"],
                        )
                    )
                return backends
        except Timeout as e:
            LOG.info(msg="create_backend timed out. {0}".format(e))
            return None

    def get_backend_by_id(self, id):
        get_url = "{0}/backends/{1}".format(self.RE_BACKEND_URL, id)
        try:
            response = req.get(
                get_url,
                timeout=(30, 30),
                headers={"X-API-KEY": self.FORC_API_KEY},
                verify=True,
            )
            try:
                data = response.json()
            except Exception as e:
                LOG.exception(e)
                return {}
            return Backend(
                id=data["id"],
                owner=data["owner"],
                location_url=data["location_url"],
                template=data["template"],
                template_version=data["template_version"],
            )
        except Timeout as e:
            LOG.info(msg="create_backend timed out. {0}".format(e))
            return None

    def delete_backend(self, id):
        delete_url = "{0}/backends/{1}".format(self.RE_BACKEND_URL, id)
        try:
            response = req.delete(
                delete_url,
                timeout=(30, 30),
                headers={"X-API-KEY": self.FORC_API_KEY},
                verify=True,
            )
            if response.status_code != 200:
                try:
                    return str(response.json())
                except json.JSONDecodeError:
                    return response.content
            elif response.status_code == 200:
                return str(True)
        except Timeout as e:
            LOG.info(msg="create_backend timed out. {0}".format(e))
            return str(-1)
        except Exception as e:
            LOG.exception(e)
            return str(-1)

    def add_user_to_backend(self, backend_id, owner_id, user_id):
        try:
            post_url = "{0}users/{1}".format(self.RE_BACKEND_URL, backend_id)
            user_info = {
                "owner": owner_id,
                "user": user_id,
            }
        except Exception as e:
            LOG.exception(e)
            return {"Error": "Could not create url or json body."}
        try:
            response = req.post(
                post_url,
                json=user_info,
                timeout=(30, 30),
                headers={"X-API-KEY": self.FORC_API_KEY},
                verify=True,
            )
            try:
                data = response.json()
            except Exception as e:
                LOG.exception(e)
                return {"Error": "Error in POST."}
            return data
        except Timeout as e:
            LOG.info(msg="create_backend timed out. {0}".format(e))
            return {"Error": "Timeout."}
        except Exception as e:
            LOG.exception(e)
            return {"Error": "An error occured."}

    def get_users_from_backend(self, backend_id):
        get_url = "{0}/users/{1}".format(self.RE_BACKEND_URL, backend_id)
        try:
            response = req.get(
                get_url,
                timeout=(30, 30),
                headers={"X-API-KEY": self.FORC_API_KEY},
                verify=True,
            )
            if response.status_code == 401:
                return ["Error: 401"]
            else:
                return response.json()
        except Timeout as e:
            LOG.info(msg="Get users for backend timed out. {0}".format(e))
            return []

    def delete_user_from_backend(self, backend_id, owner_id, user_id):
        delete_url = "{0}/users/{1}".format(self.RE_BACKEND_URL, backend_id)
        user_info = {
            "owner": owner_id,
            "user": user_id,
        }
        try:
            response = req.delete(
                delete_url,
                json=user_info,
                timeout=(30, 30),
                headers={"X-API-KEY": self.FORC_API_KEY},
                verify=True,
            )
            return response.json()
        except Timeout as e:
            LOG.info(msg="Delete user from backend timed out. {0}".format(e))
            return {"Error": "Timeout."}
        except Exception as e:
            LOG.exception(e)
            return {"Error": "An Exception occured."}

    def exist_server(self, name):
        if self.conn.compute.find_server(name) is not None:
            return True
        else:
            return False

    def get_template_version_for(self, template):
        return self.FORC_ALLOWED[template][0]

    def get_templates(self):
        return []

    # Todo test this method
    def get_allowed_templates(self):
        templates_metada = []
        # Todo load Metadata from multiple folders
        for file in os.listdir(PLAYBOOKS_DIR):
            if "_metadata.yml" in file:
                with open(PLAYBOOKS_DIR + file) as template_metadata:
                    try:
                        loaded_metadata = yaml.load(
                            template_metadata, Loader=yaml.FullLoader
                        )
                        template_name = loaded_metadata[TEMPLATE_NAME]
                        if loaded_metadata["needs_forc_support"]:
                            if template_name in list(self.FORC_ALLOWED.keys()):
                                templates_metada.append(json.dumps(loaded_metadata))
                                if template_name not in self.ALL_TEMPLATES:
                                    ALL_TEMPLATES.append(template_name)
                            else:
                                LOG.info(
                                    "Failed to find supporting FORC file for "
                                    + str(template_name)
                                )
                        else:
                            templates_metada.append(json.dumps(loaded_metadata))
                            if template_name not in self.ALL_TEMPLATES:
                                ALL_TEMPLATES.append(template_name)

                    except Exception as e:
                        LOG.exception(
                            "Failed to parse Metadata yml: " + file + "\n" + str(e)
                        )
        return templates_metada

    def get_templates_by_template(self, template_name):
        get_url = "{0}/templates/{1}".format(self.RE_BACKEND_URL, template_name)
        try:
            response = req.get(
                get_url,
                timeout=(30, 30),
                headers={"X-API-KEY": self.FORC_API_KEY},
                verify=True,
            )
            if response.status_code == 401:
                return [response.json()]
            else:
                return response.json()
        except Timeout as e:
            LOG.info(msg="get_templates_by_template timed out. {0}".format(e))
            return None

    def check_template(self, template_name, template_version):
        get_url = "{0}/templates/{1}/{2}".format(
            self.RE_BACKEND_URL, template_name, template_version
        )
        try:
            response = req.get(
                get_url,
                timeout=(30, 30),
                headers={"X-API-KEY": self.FORC_API_KEY},
                verify=True,
            )
            if response.status_code == 401:
                return [response.json()]
            else:
                return response.json()
        except Timeout as e:
            LOG.info(msg="check_template timed out. {0}".format(e))
            return None

    def get_playbook_logs(self, openstack_id):
        global active_playbooks
        LOG.info(f"Get Playbook logs {openstack_id}")
        if self.redis.exists(openstack_id) == 1 and openstack_id in active_playbooks:
            key_name = self.redis.hget(openstack_id, "name").decode("utf-8")
            playbook = active_playbooks.pop(openstack_id)
            status, stdout, stderr = playbook.get_logs()
            LOG.info(f" Playbook logs{openstack_id} stattus: {status}")

            playbook.cleanup(openstack_id)
            self.delete_keypair(key_name=key_name)
            return PlaybookResult(status=status, stdout=stdout, stderr=stderr)
        else:
            return PlaybookResult(status=-2, stdout="", stderr="")

    def get_volumes_by_ids(self, volume_ids):
        LOG.info("Get Volumes {}".format(volume_ids))

        volumes = []
        for id in volume_ids:
            try:
                os_volume = self.conn.get_volume_by_id(id=id)
                if os_volume.attachments:
                    device = os_volume.attachments[0].device
                else:
                    device = None
                LOG.info(os_volume)
                thrift_volume = Volume(
                    status=os_volume.status,
                    id=os_volume.id,
                    name=os_volume.name,
                    description=os_volume.description,
                    created_at=os_volume.created_at,
                    device=device,
                    size=os_volume.size,
                )
                volumes.append(thrift_volume)

            except Exception:
                LOG.exception("Could not find volume {}".format(id))

        return volumes

    def get_volume(self, volume_id):
        LOG.info("Get Volume {}".format(volume_id))
        try:

            os_volume = self.conn.get_volume_by_id(id=volume_id)
            LOG.info(os_volume)
            if os_volume.attachments:
                device = os_volume.attachments[0].device
            else:
                device = None

            thrift_volume = Volume(
                status=os_volume.status,
                id=os_volume.id,
                name=os_volume.name,
                description=os_volume.description,
                created_at=os_volume.created_at,
                device=device,
                size=os_volume.size,
            )
            return thrift_volume
        except Exception:
            LOG.exception("Could not find volume {}".format(id))
            return Volume(status=self.NOT_FOUND)

    def attach_volume_to_server(self, openstack_id, volume_id):
        """
        Attach volume to server.

        :param openstack_id: Id of server
        :param volume_id: Id of volume
        :return: True if attached, False if not
        """

        server = self.conn.compute.get_server(openstack_id)
        if server is None:
            LOG.exception("No Server  {0} ".format(openstack_id))
            raise serverNotFoundException(Reason="No Server {0}".format(openstack_id))

        LOG.info(
            "Attaching volume {0} to virtualmachine {1}".format(volume_id, openstack_id)
        )
        try:
            attachment = self.conn.compute.create_volume_attachment(
                server=server, volumeId=volume_id
            )
            return {"device": attachment["device"]}
        except ConflictException as e:
            LOG.exception(
                "Trying to attach volume {0} to vm {1} error : {2}".format(
                    volume_id, openstack_id, e
                ),
                exc_info=True,
            )
            raise conflictException(Reason="409")
        except Exception as e:
            LOG.exception(
                "Trying to attach volume {0} to vm {1} error : {2}".format(
                    volume_id, openstack_id, e
                ),
                exc_info=True,
            )
            return {"error": e}

    def check_server_status(self, openstack_id):
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
        LOG.info("Check Status VM {0}".format(openstack_id))
        try:
            server = self.conn.compute.get_server(openstack_id)
        except Exception:
            LOG.exception("No Server with id  {0} ".format(openstack_id))
            return VM(status=self.NOT_FOUND)

        if server is None:
            LOG.exception("No Server with id {0} ".format(openstack_id))
            return VM(status=self.NOT_FOUND)

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

                    if self.redis.exists(openstack_id) == 1:
                        global active_playbooks
                        if openstack_id in active_playbooks:
                            playbook = active_playbooks[openstack_id]
                            playbook.check_status(openstack_id)
                        status = self.redis.hget(openstack_id, "status").decode("utf-8")
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
                # server.status = self.BUILD
                return server
        except Exception as e:
            LOG.exception("Check Status VM {0} error: {1}".format(openstack_id, e))
            return VM(status=self.ERROR)

    def openstack_server_to_thrift_server(self, server):
        LOG.info("Convert server {} to thrift server".format(server))
        fixed_ip = None
        floating_ip = None
        diskspace = 0

        if server["os-extended-volumes:volumes_attached"]:
            volume_id = server["os-extended-volumes:volumes_attached"][0]["id"]
            try:
                diskspace = self.conn.block_storage.get_volume(volume_id).to_dict()[
                    "size"
                ]
            except Exception as e:
                LOG.exception("Could not found volume {}: {}".format(volume_id, e))

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
            LOG.exception(e)
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
        LOG.info("Get all servers")
        servers = self.conn.list_servers()
        LOG.info("Found {} servers".format(len(servers)))
        server_list = []
        for server in servers:
            try:
                thrift_server = self.openstack_server_to_thrift_server(server)
                server_list.append(thrift_server)

            except Exception as e:
                LOG.exception("Could not transform to thrift_server: {}".format(e))
        LOG.info(
            "Converted {} servers to thrift_server objects".format(len(server_list))
        )
        # LOG.info(server_list)
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
        LOG.info("Setting up UDP security group for {0}".format(server_id))
        server = self.conn.get_server(name_or_id=server_id)
        if server is None:
            LOG.exception("Instance {0} not found".format(server_id))
            raise serverNotFoundException
        sec = self.conn.get_security_group(name_or_id=server.name + "_udp")
        if sec:
            LOG.info(
                "UDP Security group with name {} already exists.".format(
                    server.name + "_udp"
                )
            )
            server_security_groups = self.conn.list_server_security_groups(server)
            for sg in server_security_groups:
                if sg["name"] == server.name + "_udp":
                    LOG.info(
                        "UDP Security group with name {} already added to server.".format(
                            server.name + "_udp"
                        )
                    )
                    return True

            self.conn.compute.add_security_group_to_server(
                server=server_id, security_group=sec
            )

            return True

        ip_base = (
            list(self.conn.compute.server_ips(server=server_id))[0]
            .to_dict()["address"]
            .split(".")[-1]
        )
        x = int(ip_base)
        udp_port_start = eval(self.UDP_PORT_CALCULATION)

        security_group = self.create_security_group(
            name=server.name + "_udp",
            udp_port_start=udp_port_start,
            udp=True,
            ssh=False,
            https=False,
            http=False,
            description="UDP",
        )
        LOG.info(security_group)
        LOG.info(
            "Add security group {} to server {} ".format(security_group.id, server_id)
        )
        self.conn.compute.add_security_group_to_server(
            server=server_id, security_group=security_group
        )

        return True

    def detach_ip_from_server(self, server_id, floating_ip):
        LOG.info(
            "Detaching floating ip {} from server {}".format(floating_ip, server_id)
        )
        try:
            self.conn.compute.remove_floating_ip_from_server(
                server=server_id, address=floating_ip
            )
            return True
        except Exception:
            LOG.exception(
                "Could not detach floating ip {} from server {}".format(
                    floating_ip, server_id
                )
            )
            return False

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
        LOG.info("Get IP and PORT for server {0}".format(openstack_id))
        server = self.get_server(openstack_id)
        server_base = server.fixed_ip.split(".")[-1]
        x = int(server_base)
        port = eval(self.SSH_PORT_CALCULATION)
        udp_port_start = eval(self.UDP_PORT_CALCULATION)
        return {"port": str(port), "udp": str(udp_port_start)}

    def terminate_cluster(self, cluster_id):
        headers = {"content-Type": "application/json"}
        body = {"mode": "openstack"}
        response = req.delete(
            url="{}terminate/{}".format(self.BIBIGRID_URL, cluster_id),
            json=body,
            headers=headers,
            verify=self.PRODUCTION,
        )
        LOG.info(response.json())
        return response.json()

    def get_cluster_status(self, cluster_id):
        LOG.info("Get Cluster {} status".format(cluster_id))
        headers = {"content-Type": "application/json"}
        body = {"mode": "openstack"}
        request_url = self.BIBIGRID_URL + "info/" + cluster_id
        response = req.get(
            url=request_url, json=body, headers=headers, verify=self.PRODUCTION
        )
        LOG.info("Cluster {} status: {} ".format(cluster_id, response.content))
        json_resp = response.json(strict=False)
        if json_resp.get("log", None):
            json_resp["log"] = str(json_resp["log"])
        if json_resp.get("msg", None):
            json_resp["msg"] = str(json_resp["msg"])

        return json_resp

    def bibigrid_available(self):
        LOG.info("Checking if Bibigrid is available")
        if not self.BIBIGIRD_EP:
            LOG.info("Bibigrid EP is not set")
            return False
        try:
            status = req.get(self.BIBIGIRD_EP + "/server/health").status_code
            if status == 200:
                LOG.info("Bibigrid Server is available")
                return True

            else:

                LOG.exception("Bibigrid is offline")
                return False

        except Exception:
            LOG.exception("Bibigrid is offline")
            return False

    def get_clusters_info(self):
        headers = {"content-Type": "application/json"}
        body = {"mode": "openstack"}
        request_url = self.BIBIGRID_URL + "list"
        response = req.get(
            url=request_url, json=body, headers=headers, verify=self.PRODUCTION
        )
        LOG.info(response.json())
        infos = response.json()["info"]
        return infos

    def scale_up_cluster(
        self, cluster_id, image, flavor, count, names, start_idx, batch_index
    ):
        cluster_info = self.get_cluster_info(cluster_id=cluster_id)
        image = self.get_image(image=image)
        flavor = self.get_flavor(flavor=flavor)
        network = self.get_network()
        openstack_ids = []
        for i in range(count):
            metadata = {
                "bibigrid-id": cluster_info.cluster_id,
                "user": cluster_info.user,
                "worker-batch": str(batch_index),
                "name": names[i],
                "worker-index": str(start_idx + i),
            }
            fileDir = os.path.dirname(os.path.abspath(__file__))
            deactivate_update_script_file = os.path.join(
                fileDir, "scripts/bash/mount.sh"
            )
            with open(deactivate_update_script_file, "r") as file:
                deactivate_update_script = file.read()
                deactivate_update_script = encodeutils.safe_encode(
                    deactivate_update_script.encode("utf-8")
                )

            LOG.info("Create cluster machine: {}".format(metadata))

            server = self.conn.create_server(
                name=names[i],
                image=image.id,
                flavor=flavor.id,
                network=[network.id],
                userdata=deactivate_update_script,
                key_name=cluster_info.key_name,
                meta=metadata,
                availability_zone=self.AVAIALABILITY_ZONE,
                security_groups=cluster_info.group_id,
            )
            LOG.info("Created cluster machine:{}".format(server["id"]))

            openstack_ids.append(server["id"])
            LOG.info(openstack_ids)

        return {"openstack_ids": openstack_ids}

    def get_cluster_info(self, cluster_id):
        infos = self.get_clusters_info()
        for info in infos:
            LOG.info(cluster_id)
            LOG.info(info)
            LOG.info(info["cluster-id"])
            LOG.info(cluster_id == info["cluster-id"])
            if info["cluster-id"] == cluster_id:
                cluster_info = ClusterInfo(
                    launch_date=info["launch date"],
                    group_id=info["group-id"],
                    network_id=info["network-id"],
                    public_ip=info["public-ip"],
                    subnet_id=info["subnet-id"],
                    user=info["user"],
                    inst_counter=info["# inst"],
                    cluster_id=info["cluster-id"],
                    key_name=info["key name"],
                )
                LOG.info("CLuster info : {}".format(cluster_info))
                return cluster_info

        return None

    def get_calculation_formulars(self):
        return {
            "ssh_port_calculation": self.SSH_FORMULAR,
            "udp_port_calculation": self.UDP_FORMULAR,
        }

    def get_gateway_ip(self):
        return {"gateway_ip": self.GATEWAY_IP}

    def start_cluster(self, public_key, master_instance, worker_instances, user):
        master_instance = master_instance.__dict__
        del master_instance["count"]
        wI = []
        for wk in worker_instances:
            LOG.info(wk)
            wI.append(wk.__dict__)
        headers = {"content-Type": "application/json"}
        body = {
            "mode": "openstack",
            "subnet": self.SUB_NETWORK,
            "sshPublicKeys": [public_key],
            "user": user,
            "sshUser": "ubuntu",
            "availabilityZone": self.AVAIALABILITY_ZONE,
            "masterInstance": master_instance,
            "workerInstances": wI,
            "useMasterWithPublicIp": False,
        }
        for mode in self.BIBIGRID_MODES:
            body.update({mode: True})
        request_url = self.BIBIGRID_URL + "create"
        response = req.post(
            url=request_url, json=body, headers=headers, verify=self.PRODUCTION
        )
        LOG.info(response.json())
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
        LOG.info(
            "Create Snapshot from Instance {0} with name {1} for {2}".format(
                openstack_id, name, elixir_id
            )
        )

        try:
            snapshot_munch = self.conn.create_image_snapshot(
                server=openstack_id, name=name
            )
        except ConflictException as e:
            LOG.exception("Create snapshot {0} error: {1}".format(openstack_id, e))

            raise conflictException(Reason="409")
        except Exception:
            LOG.exception("Instance {0} not found".format(openstack_id))
            return
        try:
            snapshot = self.conn.get_image_by_id(snapshot_munch["id"])
            snapshot_id = snapshot["id"]
            # todo check again
            try:
                image = self.conn.get_image(name_or_id=snapshot_id)
                if description:
                    self.conn.update_image_properties(
                        image=image, meta={"description": description}
                    )

                for tag in base_tags:
                    self.conn.image.add_tag(image=snapshot_id, tag=tag)
            except Exception:
                LOG.exception("Tag error catched")
            try:
                self.conn.image.add_tag(image=snapshot_id, tag=elixir_id)
            except Exception:
                LOG.exception(
                    f"Could not add Tag {elixir_id} to Snapshot: {snapshot_id}"
                )

            return snapshot_id
        except Exception as e:
            LOG.exception(
                "Create Snapshot from Instance {0}"
                " with name {1} for {2} error : {3}".format(
                    openstack_id, name, elixir_id, e
                )
            )
            return None

    def delete_image(self, image_id):
        """
        Delete Image.

        :param image_id: Id of the image
        :return: True if deleted, False if not
        """
        LOG.info("Delete Image {0}".format(image_id))
        try:
            image = self.conn.compute.get_image(image_id)
            if image is None:
                LOG.exception("Image {0} not found!".format(image))
                raise imageNotFoundException(
                    Reason=("Image {0} not found".format(image))
                )
            self.conn.compute.delete_image(image)
            return True
        except Exception as e:
            LOG.exception("Delete Image {0} error : {1}".format(image_id, e))
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
                LOG.exception("Instance {0} not found".format(openstack_id))
                raise serverNotFoundException
            LOG.info("Checking if Server already got an Floating Ip")
            for values in server.addresses.values():
                for address in values:
                    if address["OS-EXT-IPS:type"] == "floating":
                        return address["addr"]
            LOG.info("Checking if unused Floating-Ip exist")

            for floating_ip in self.conn.network.ips():
                if not floating_ip.fixed_ip_address:
                    self.conn.compute.add_floating_ip_to_server(
                        server, floating_ip.floating_ip_address
                    )
                    LOG.info(
                        "Adding existing Floating IP {0} to {1}".format(
                            str(floating_ip.floating_ip_address), openstack_id
                        )
                    )
                    return str(floating_ip.floating_ip_address)

            networkID = self.conn.network.find_network(network)
            if networkID is None:
                LOG.exception("Network " + network + " not found")
                raise networkNotFoundException
            networkID = networkID.to_dict()["id"]
            floating_ip = self.conn.network.create_ip(floating_network_id=networkID)
            floating_ip = self.conn.network.get_ip(floating_ip)
            self.conn.compute.add_floating_ip_to_server(
                server, floating_ip.floating_ip_address
            )

            return floating_ip
        except Exception as e:
            LOG.exception(
                "Adding Floating IP to {0} with network {1} error:{2}".format(
                    openstack_id, network, e
                )
            )
            return None

    def netcat(self, host, port):
        """
        Try to connect to specific host:port.

        :param host: Host to connect
        :param port: Port to connect
        :return: True if successfully connected, False if not
        """
        LOG.info("Checking SSH Connection {0}:{1}".format(host, port))
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            r = sock.connect_ex((host, port))
            LOG.info(
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
        LOG.info(f"Delete Server {openstack_id}")
        try:
            server = self.conn.get_server(name_or_id=openstack_id)

            if server is None:
                server = self.conn.compute.get_server(openstack_id)
                if server is None:
                    LOG.error("Instance {0} not found".format(openstack_id))
                    return False
            task_state = self.check_server_task_state(openstack_id)
            if (
                task_state == "image_snapshot"
                or task_state == "image_pending_upload"
                or task_state == "image_uploading"
            ):
                raise ConflictException("task_state in image creating")
            security_groups = self.conn.list_server_security_groups(server=server)
            LOG.info(security_groups)
            security_groups = [
                sec
                for sec in security_groups
                if sec.name != self.DEFAULT_SECURITY_GROUP
                and not "bibigrid" in sec.name
            ]
            if security_groups is not None:
                for sg in security_groups:
                    LOG.info("Delete security group {0}".format(sg.name))
                    self.conn.compute.remove_security_group_from_server(
                        server=server, security_group=sg
                    )
                    self.conn.network.delete_security_group(sg)
                self.conn.compute.delete_server(server)
            else:
                return False

            return True
        except ConflictException as e:
            LOG.exception("Delete Server {0} error: {1}".format(openstack_id, e))

            raise conflictException(Reason="409")
        except Exception as e:
            LOG.exception("Delete Server {0} error: {1}".format(openstack_id, e))
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
                    LOG.info(
                        "Delete Volume Attachment  {0}".format(volume_attachment_id)
                    )
                    self.conn.compute.delete_volume_attachment(
                        volume_attachment=volume_attachment_id, server=server_id
                    )
            return True
        except ConflictException as e:
            LOG.exception(
                f"Delete volume attachment (server: {server_id} volume: {volume_id}) error"
            )

            raise conflictException(Reason="409")
        except Exception as e:
            LOG.exception(f"Delete Volume Attachment  {volume_attachment_id} error")
            return False

    def delete_volume(self, volume_id):
        """
        Delete volume.

        :param volume_id: Id of the volume
        :return: True if deleted, False if not
        """

        try:
            LOG.info("Delete Volume  {0}".format(volume_id))
            self.conn.block_storage.delete_volume(volume=volume_id)
            return True
        except ConflictException as e:
            LOG.exception(f"Delete volume {volume_id} error")

            raise conflictException(Reason="409")
        except Exception as e:
            LOG.exception(f"Delete Volume {volume_id} error")
            return False

    def stop_server(self, openstack_id):
        """
        Stop server.

        :param openstack_id: Id of the server.
        :return: True if resumed, False if not
        """
        LOG.info(f"Stop Server {openstack_id}")
        server = self.conn.compute.get_server(openstack_id)
        try:
            if server is None:
                LOG.exception(f"Instance {openstack_id} not found")
                raise serverNotFoundException

            if server.status == self.ACTIVE:
                self.conn.compute.stop_server(server)
                return True
            else:
                return False
        except ConflictException as e:
            LOG.exception(f"Stop Server {openstack_id} error")

            raise conflictException(Reason="409")
        except Exception as e:
            LOG.exception(f"Stop Server {openstack_id} error:")

            return False

    def reboot_server(self, server_id, reboot_type):
        """
        Reboot server.

        :param server_id: Id of the server
        :param reboot_type: HARD or SOFT
        :return:  True if resumed, False if not
        """
        LOG.info("Reboot Server {} {}".format(server_id, reboot_type))
        try:
            server = self.conn.compute.get_server(server_id)
            if server is None:
                LOG.exception("Instance {0} not found".format(server_id))
                raise serverNotFoundException
            else:
                self.conn.compute.reboot_server(server, reboot_type)
                return True
        except ConflictException as e:
            LOG.exception(f"Reboot Server {server_id} error")

            raise conflictException(Reason="409")
        except Exception as e:
            LOG.exception(f"Reboot Server {server_id} {reboot_type} Error")
            return False

    def resume_server(self, openstack_id):
        """
        Resume stopped server.

        :param openstack_id: Id of the server.
        :return: True if resumed, False if not
        """
        LOG.info("Resume Server {0}".format(openstack_id))
        try:
            server = self.conn.compute.get_server(openstack_id)
            if server is None:
                LOG.exception("Instance {0} not found".format(openstack_id))
                raise serverNotFoundException
            if server.status == self.SHUTOFF:
                self.conn.compute.start_server(server)
                return True
            else:
                return False
        except ConflictException:
            LOG.exception(f"Resume Server {openstack_id} error")

            raise conflictException(Reason="409")
        except Exception:
            LOG.exception(f"Resume Server {openstack_id} error:")
            return False

    def create_security_group(
        self,
        name,
        udp_port_start=None,
        ssh=True,
        http=False,
        https=False,
        udp=False,
        description=None,
        resenv=[],
    ):
        LOG.info("Create new security group {}".format(name))
        sec = self.conn.get_security_group(name_or_id=name)
        if sec:
            LOG.info("Security group with name {} already exists.".format(name))
            return sec
        new_security_group = self.conn.create_security_group(
            name=name, description=description
        )
        if http:
            LOG.info("Add http rule to security group {}".format(name))
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
            LOG.info("Add https rule to security group {}".format(name))

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
            LOG.info(
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
            LOG.info("Add ssh rule to security group {}".format(name))

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
        for research_enviroment in resenv:
            if research_enviroment in self.loaded_resenv_metadata:
                LOG.info(
                    "Add "
                    + research_enviroment
                    + " rule to security group {}".format(name)
                )
                resenv_metadata = self.loaded_resenv_metadata[research_enviroment]
                self.conn.network.create_security_group_rule(
                    direction=resenv_metadata.direction,
                    protocol=resenv_metadata.protocol,
                    port_range_max=resenv_metadata.port,
                    port_range_min=resenv_metadata.port,
                    security_group_id=new_security_group["id"],
                )
            elif research_enviroment != "user_key_url":
                # Todo add mail for this logging as this should not happen
                LOG.error(
                    "Error: Could not find metadata for research enviroment: "
                    + research_enviroment
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
        LOG.info("Get Limits")
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

    def update_playbooks(self):
        if self.GITHUB_PLAYBOOKS_REPO is None:
            LOG.info(
                "Github playbooks repo url is None. Aborting download of playbooks."
            )
            return
        LOG.info("STARTED update of playbooks")
        r = req.get(self.GITHUB_PLAYBOOKS_REPO)
        contents = json.loads(r.content)
        # Todo maybe clone entire direcotry
        for f in contents:
            if f["name"] != "LICENSE":
                LOG.info("started download of " + f["name"])
                download_link = f["download_url"]
                file_request = req.get(download_link)
                filename = "/code/VirtualMachineService/ancon/playbooks/" + f["name"]
                with open(filename, "w") as playbook_file:
                    playbook_file.write(file_request.content.decode("utf-8"))
        templates_metadata = self.load_resenv_metadata()
        for template_metadata in templates_metadata:
            try:
                metadata = ResenvMetadata(
                    template_metadata[TEMPLATE_NAME],
                    template_metadata[PORT],
                    template_metadata[SECURITYGROUP_NAME],
                    template_metadata[SECURITYGROUP_DESCRIPTION],
                    template_metadata[SECURITYGROUP_SSH],
                    template_metadata[DIRECTION],
                    template_metadata[PROTOCOL],
                    template_metadata[INFORMATION_FOR_DISPLAY],
                )
                self.update_forc_allowed(template_metadata)
                if metadata.name not in list(self.loaded_resenv_metadata.keys()):
                    self.loaded_resenv_metadata[metadata.name] = metadata
                else:
                    if self.loaded_resenv_metadata[metadata.name] != metadata:
                        self.loaded_resenv_metadata[metadata.name] = metadata

            except Exception as e:
                LOG.exception(
                    "Failed to parse Metadata yml: "
                    + str(template_metadata)
                    + "\n"
                    + str(e)
                )

    def load_resenv_metadata(self):
        templates_metada = []
        for file in os.listdir(PLAYBOOKS_DIR):
            if "_metadata.yml" in file:
                with open(PLAYBOOKS_DIR + file) as template_metadata:
                    try:
                        loaded_metadata = yaml.load(
                            template_metadata, Loader=yaml.FullLoader
                        )
                        template_name = loaded_metadata[TEMPLATE_NAME]

                        templates_metada.append(loaded_metadata)
                        if template_name not in self.ALL_TEMPLATES:
                            ALL_TEMPLATES.append(template_name)
                    except Exception as e:
                        LOG.exception(
                            "Failed to parse Metadata yml: " + file + "\n" + str(e)
                        )
        return templates_metada

    def update_forc_allowed(self, template_metadata):
        if template_metadata["needs_forc_support"]:
            name = template_metadata[TEMPLATE_NAME]
            allowed_versions = []
            for forc_version in template_metadata[FORC_VERSIONS]:
                get_url = "{0}/templates/{1}/{2}".format(
                    self.RE_BACKEND_URL, name, forc_version
                )
                try:
                    response = req.get(
                        get_url,
                        timeout=(30, 30),
                        headers={"X-API-KEY": self.FORC_API_KEY},
                        verify=True,
                    )
                    if response.status_code == 200:
                        allowed_versions.append(forc_version)
                except Timeout as e:
                    LOG.info(msg="checking template/version timed out. {0}".format(e))
            allowed_versions.sort(key=LooseVersion)
            allowed_versions.reverse()
            self.FORC_ALLOWED[name] = allowed_versions


class ResenvMetadata:
    def __init__(
        self,
        name,
        port,
        security_group_name,
        security_group_description,
        security_group_ssh,
        direction,
        protocol,
        information_for_display,
    ):
        self.name = name
        self.port = port
        self.security_group_name = security_group_name
        self.security_group_description = security_group_description
        self.security_group_ssh = security_group_ssh
        self.direction = direction
        self.protocol = protocol
        self.information_for_display = information_for_display
