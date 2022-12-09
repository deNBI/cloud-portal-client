"""
This Module implements an VirtualMachineHandler.

Which can be used for the PortalClient.
"""
import math
import sys
import zipfile
from uuid import uuid4
from typing import List

try:
    from ancon.Playbook import ALL_TEMPLATES, Playbook
    from constants import VERSION
    from ttypes import (
        VM,
        Backend,
        ClusterInfo,
        Flavor,
        Image,
        PlaybookResult,
        Volume,
        authenticationException,
        conflictException,
        flavorNotFoundException,
        imageNotFoundException,
        networkNotFoundException,
        otherException,
        ressourceException,
        serverNotFoundException,
    )

    from VirtualMachineService import Iface

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
import glob
import json
import logging
import os
import shutil
import socket
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
import openstack
from openstack.compute.v2.server import Server
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
NEEDS_FORC_SUPPORT = "needs_forc_support"
FORC_VERSIONS = "forc_versions"

openstack.enable_logging(debug=False)


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
    TEMPLATES_URL = "templates"
    BACKENDS_URL = "backends"
    BACKENDS_BY_OWNER_URL = f"{BACKENDS_URL}/byOwner"
    BACKENDS_BY_TEMPLATE_URL = f"{BACKENDS_URL}/byTemplate"
    USERS_URL = "users"
    ALL_TEMPLATES = ALL_TEMPLATES
    loaded_resenv_metadata = {}

    def keyboard_interrupt_handler_playbooks(self):
        global active_playbooks
        for k, v in active_playbooks.items():
            LOG.info(f"Clearing traces of Playbook-VM for (openstack_id): {k}")
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
            self.DEFAULT_SECURITY_GROUP_NAME = "defaultSimpleVM"
            self.DEFAULT_SECURITY_GROUPS = [self.DEFAULT_SECURITY_GROUP_NAME]
            self.GATEWAY_SECURITY_GROUP_ID = cfg["openstack_connection"][
                "gateway_security_group_id"
            ]

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
                self.BIBIGRID_DEACTIVATE_UPRADES_SCRIPT = (
                    self.create_deactivate_update_script()
                )
                self.BIBIGRID_ANSIBLE_ROLES = cfg["bibigrid"].get(
                    "ansibleGalaxyRoles", []
                )
                LOG.info(
                    f"Loaded Ansible Galaxy Roles for Bibigrid:\n {self.BIBIGRID_ANSIBLE_ROLES}"
                )

                LOG.info(msg=f"Bibigrd url loaded: {self.BIBIGRID_URL}")
            except Exception as e:
                LOG.exception(e)
                LOG.info("Bibigrid not loaded.")
                self.BIBIGRID_URL = None
                self.SUB_NETWORK = None

            try:
                self.RE_BACKEND_URL = cfg["forc"]["forc_url"]
                self.FORC_API_KEY = os.environ.get("FORC_API_KEY", None)
                self.FORC_ALLOWED = {}
                self.FORC_REMOTE_ID = cfg["forc"]["forc_remote_id"]
                self.GITHUB_PLAYBOOKS_REPO = cfg["forc"]["github_playbooks_repo"]
                if (
                    not self.RE_BACKEND_URL
                    or not self.FORC_API_KEY
                    or not self.GITHUB_PLAYBOOKS_REPO
                ):
                    raise ValueError
                LOG.info(msg=f"Forc-Backend url loaded: {self.RE_BACKEND_URL}")
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

                LOG.info(f"Gateway IP is {self.GATEWAY_IP}")
        self.update_playbooks()
        self.conn = self.create_connection()
        self.validate_gateway_security_group()
        self.create_or_get_default_ssh_security_group()

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
                LOG.exception(f"Set Password for user {user} failed : {str(e)}")
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
            LOG.exception(f"Get Flavors Error: {e}")
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
            LOG.exception(f"Compare Version Error: {e}")
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

                properties = img.get("properties")
                if not properties:
                    properties = {}
                    LOG.warning(f"Could not get properties for img: {img}")
                description = properties.get("description", "")
                tags = img.get("tags", [])
                LOG.info(set(self.ALL_TEMPLATES).intersection(tags))
                if len(
                    set(self.ALL_TEMPLATES).intersection(tags)
                ) > 0 and not self.cross_check_forc_image(tags):
                    LOG.info(f"Resenv check: Skipping {img['name']}.")
                    continue
                image_type = properties.get("image_type", "image")
                if description is None:
                    LOG.warning("No Description and  for " + img["name"])

                image = Image(
                    name=img["name"],
                    min_disk=img["min_disk"],
                    min_ram=img["min_ram"],
                    status=img["status"],
                    os_version=img.get("os_version", ""),
                    os_distro=img.get("os_distro", ""),
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
            LOG.exception(f"Get Images Error: {e}")
            return ()

    def prepare_image(self, img):
        try:
            properties = img.get("properties")
            if not properties:
                properties = {}
                LOG.warning(f"No properties found in image: {img}")
            description = properties.get("description", "")
            tags = img.get("tags", [])
            LOG.info(set(self.ALL_TEMPLATES).intersection(tags))
            if len(
                set(self.ALL_TEMPLATES).intersection(tags)
            ) > 0 and not self.cross_check_forc_image(tags):
                LOG.info(f"Resenv check: Skipping {img['name']}.")
                return None
            image_type = properties.get("image_type", "image")
            if description is None:
                LOG.warning("No Description for " + img["name"])

            image = Image(
                name=img["name"],
                min_disk=img["min_disk"],
                min_ram=img["min_ram"],
                status=img["status"],
                os_version=img.get("os_version", ""),
                os_distro=img.get("os_distro", ""),
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
            LOG.exception(f"Prepare image Error: {e}")
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
            LOG.exception(f"Get Images Error: {e}")
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
            LOG.exception(f"Get Images Error: {e}")
            return ()

    def get_Image_with_Tag(self, id):
        """
        Get Image with Tags.

        :param id: Id of the image
        :return: Image instance
        """
        LOG.info(f"Get Image {id} with tags")
        try:
            img = self.conn.get_image(name_or_id=id)
            if not img:
                return Image()
            properties = img.get("properties")
            if not properties:
                properties = {}
                LOG.warning(f"Could not get properties for image: {img}")
            description = properties.get("description", "")
            tags = img.get("tags", [])
            image = Image(
                name=img["name"],
                min_disk=img["min_disk"],
                min_ram=img["min_ram"],
                status=img["status"],
                os_version=img.get("os_version", ""),
                os_distro=img.get("os_distro", ""),
                created_at=img["created_at"],
                updated_at=img["updated_at"],
                openstack_id=img["id"],
                description=description,
                tag=tags,
            )
            return image
        except Exception as e:
            LOG.exception(f"Get Image {id} with Tag Error: {e}")
            return Image()

    def get_Images_by_filter(self, filter_list):
        """
        Get filtered Images.

        :return: List of image instances.
        """
        LOG.info(f"Get filtered Images: {filter_list}")
        images = list()
        try:
            for img in filter(
                lambda x: "tags" in x
                and len(x["tags"]) > 0
                and x["status"] == "active",
                self.conn.list_images(),
            ):
                tags = img.get("tags", [])
                if "resenv" in filter_list:
                    modes = filter_list["resenv"].split(",")
                    LOG.info(modes)
                    if "resenv" in tags and not self.cross_check_forc_image(tags):
                        continue
                properties = img.get("properties")
                if not properties:
                    properties = {}
                    LOG.warning(f"Could not get properties for img: {img}")
                description = properties.get("description", "")
                image_type = properties.get("image_type", "image")
                if description is None:
                    LOG.warning(f"No Description for {img['name']}")

                image = Image(
                    name=img["name"],
                    min_disk=img["min_disk"],
                    min_ram=img["min_ram"],
                    status=img["status"],
                    created_at=img["created_at"],
                    updated_at=img["updated_at"],
                    os_version=img.get("os_version", ""),
                    os_distro=img.get("os_distro", ""),
                    openstack_id=img["id"],
                    description=description,
                    tag=tags,
                    is_snapshot=image_type == "snapshot",
                )
                LOG.info(image)

                images.append(image)

            return images
        except Exception as e:
            LOG.exception(f"Get Images Error: {e}")
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
                LOG.info(f"Create Keypair {keyname}")

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
            LOG.exception(f"Import Keypair {keyname} error:{e}")
            return None

    @staticmethod
    def openstack_flav_to_thrift_flav(flavor):
        try:
            if "name" in flavor:
                name = flavor["name"]
            elif "original_name" in flavor:
                name = flavor["original_name"]
            else:
                name = "NoNameFound"

            flav = Flavor(
                vcpus=flavor["vcpus"],
                ram=flavor["ram"],
                disk=flavor["disk"],
                name=name,
                openstack_id=None,
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

    def get_server(self, openstack_id: str) -> VM:
        """
        Get a server.

        :param openstack_id: Id of the server
        :return: Server instance
        """
        floating_ip = None  # noqa
        fixed_ip = None  # noqa
        LOG.info(f"Get Server {openstack_id}")
        try:
            server: Server = self.conn.get_server_by_id(openstack_id)
            return self.openstack_server_to_thrift_server(server=server)
        except Exception as e:
            LOG.exception(f"No Server found {openstack_id} | Error {e}")
            return VM(status=self.NOT_FOUND)

    def get_servers_by_ids(self, ids):
        servers = []
        for id in ids:
            LOG.info(f"Get server {id}")
            try:
                server = self.conn.get_server_by_id(id)
                servers.append(server)
            except Exception as e:
                LOG.exception(f"Requested VM {id} not found!\n {e}")
        server_list = []
        for server in servers:
            if server:
                server_list.append(self.openstack_server_to_thrift_server(server))
        return server_list

    def check_server_task_state(self, openstack_id):
        LOG.info(f"Checking Task State: {openstack_id}")
        server = self.conn.get_server_by_id(openstack_id)
        if not server:
            return "No server found"
        task_state = server.get("task_state", None)
        LOG.info(f"Task State: {task_state}")
        if task_state:
            return task_state
        else:
            return "No active task"

    def get_image(self, image):
        image = self.conn.get_image(name_or_id=image)

        if image is None:
            LOG.exception(f"Image {image} not found!")
            raise imageNotFoundException(Reason=f"Image {image} not found")
        return image

    def get_flavor(self, flavor):
        flavor = self.conn.compute.find_flavor(flavor)
        if flavor is None:
            LOG.exception(f"Flavor {flavor} not found!")
            raise flavorNotFoundException(Reason=f"Flavor {flavor} not found!")
        return flavor

    def get_network(self):
        network = self.conn.network.find_network(self.NETWORK)
        if network is None:
            LOG.exception(f"Network {network} not found!")
            raise networkNotFoundException(Reason=f"Network {network} not found!")
        return network

    def create_add_keys_script(self, keys):
        LOG.info("create add key script")
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
        LOG.info(f"create init script for volume ids:{volume_ids_path_new}")
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
            LOG.info(f"New Token: {self.API_TOKEN}")
        else:
            LOG.info("Check existing token")
            now = datetime.datetime.now()
            # some buffer
            now = now - datetime.timedelta(minutes=self.API_TOKEN_BUFFER)
            api_token_expires_at = self.API_TOKEN["expires_at"]
            if now.time() > api_token_expires_at.time():
                expired_since = api_token_expires_at - now
                LOG.info(
                    f"Old token is expired since {expired_since.seconds // 60} minutes!"
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
        LOG.info(f"Creating volume with {volume_storage} GB diskspace")

        try:
            volume = self.conn.block_storage.create_volume(
                name=volume_name, size=volume_storage, metadata=metadata
            )
            LOG.info(volume)
            return {"volume_id": volume["id"]}
        except Exception as e:
            LOG.exception(
                f"Trying to create volume with {volume_storage} GB  error : {e}",
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
            LOG.exception(f"Start Server {servername} error:{e}")
            return {}

    def prepare_security_groups_new_server(
        self,
        resenv: List[str],
        servername: str,
        http: bool = False,
        https: bool = False,
    ):
        custom_security_groups = []

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
            elif research_enviroment not in ["user_key_url", "optional"]:
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
        LOG.info(f"Start Server {servername}")
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
            LOG.exception(f"Start Server {servername} error:{e}")
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
        LOG.info(f"Start Server {servername}")
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
            LOG.exception(f"Start Server {servername} error:{e}")
            return {}

    def create_resenv_security_group_and_attach_to_server(
        self, server_id: str, resenv_template: str
    ):
        LOG.info(f"Create {resenv_template} Security Group for Instance: {server_id}")

        server = self.conn.get_server(name_or_id=server_id)

        if server is None:
            LOG.exception(f"Instance {server_id} not found")
            raise serverNotFoundException
        resenv_metadata = self.loaded_resenv_metadata[resenv_template]
        resenv_security_group = self.conn.get_security_group(
            name_or_id=server.name + resenv_metadata.security_group_name
        )
        if not resenv_security_group:
            self.prepare_security_groups_new_server(
                resenv=[resenv_template], servername=server.name
            )
            resenv_security_group = self.conn.get_security_group(
                name_or_id=server.name + resenv_metadata.security_group_name
            )
        if resenv_security_group:
            server_security_groups = self.conn.list_server_security_groups(server)
            for sg in server_security_groups:
                if sg["name"] == resenv_security_group.name:
                    return
            LOG.info(
                f"Add {resenv_security_group} Security Groups to Instance: {server_id}"
            )

            self.conn.compute.add_security_group_to_server(
                server=server_id, security_group=resenv_security_group
            )

    def create_resenv_security_group(self, resenv_template: str):
        if resenv_template in self.loaded_resenv_metadata:
            resenv_metadata = self.loaded_resenv_metadata[research_enviroment]

            return self.create_security_group(
                name=servername + resenv_metadata.security_group_name,
                resenv=resenv,
                description=resenv_metadata.security_group_description,
                ssh=resenv_metadata.security_group_ssh,
            )
        return None

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
        LOG.info(f"Start Server {servername} with custom key")
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
            LOG.exception(f"Start Server {servername} error:{e}")
            return {}

    def create_and_deploy_playbook(
        self, public_key, playbooks_information, openstack_id
    ):
        global active_playbooks
        LOG.info(
            msg=f"Starting Playbook for (openstack_id): {openstack_id} --> {playbooks_information}"
        )
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
            url = self.RE_BACKEND_URL.split(":")
            return f"https:{url[1]}/"

    def cross_check_forc_image(self, tags):
        get_url = f"{self.RE_BACKEND_URL}{self.TEMPLATES_URL}"
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
            LOG.error(f"Could not get templates from FORC.\n {e}")
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
            post_url = f"{self.RE_BACKEND_URL}{self.BACKENDS_URL}"
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
            LOG.info(msg=f"create_backend timed out. {e}")
            return {}
        except Exception as e:
            LOG.exception(e)
            return {}

    def get_backends(self):
        get_url = f"{self.RE_BACKEND_URL}{self.BACKENDS_URL}"
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
            LOG.info(msg=f"create_backend timed out. {e}")
            return None

    def get_backends_by_owner(self, elixir_id):
        get_url = f"{self.RE_BACKEND_URL}{self.BACKENDS_BY_OWNER_URL}/{elixir_id}"
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
            LOG.info(msg=f"create_backend timed out. {e}")
            return None

    def get_backends_by_template(self, template):
        get_url = f"{self.RE_BACKEND_URL}{self.BACKENDS_BY_TEMPLATE_URL}/{template}"
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
            LOG.info(msg=f"create_backend timed out. {e}")
            return None

    def get_backend_by_id(self, id):
        get_url = f"{self.RE_BACKEND_URL}{self.BACKENDS_URL}/{id}"
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
            LOG.info(msg=f"create_backend timed out. {e}")
            return None

    def delete_backend(self, id):
        delete_url = f"{self.RE_BACKEND_URL}{self.BACKENDS_URL}/{id}"
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
            LOG.info(msg=f"create_backend timed out. {e}")
            return str(-1)
        except Exception as e:
            LOG.exception(e)
            return str(-1)

    def add_user_to_backend(self, backend_id, user_id):
        try:
            post_url = f"{self.RE_BACKEND_URL}{self.USERS_URL}/{backend_id}"
            user_info = {
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
            LOG.info(msg=f"create_backend timed out. {e}")
            return {"Error": "Timeout."}
        except Exception as e:
            LOG.exception(e)
            return {"Error": "An error occured."}

    def get_users_from_backend(self, backend_id):
        get_url = f"{self.RE_BACKEND_URL}{self.USERS_URL}/{backend_id}"
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
                user_list = []
                users = response.json()
                for user in users:
                    if user.get("user", None):
                        user_list.append(user["user"])
                return user_list
        except Timeout as e:
            LOG.info(msg=f"Get users for backend timed out. {e}")
            return []

    def delete_user_from_backend(self, backend_id, user_id):
        delete_url = f"{self.RE_BACKEND_URL}{self.USERS_URL}/{backend_id}"
        user_info = {
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
            LOG.info(msg=f"Delete user from backend timed out. {e}")
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

    def get_allowed_templates(self):
        templates_metadata = []
        for key, value in self.loaded_resenv_metadata.items():
            if value.needs_forc_support:
                templates_metadata.append(value.json_string)
        return templates_metadata

    def get_templates_by_template(self, template_name):
        get_url = f"{self.RE_BACKEND_URL}{self.TEMPLATES_URL}/{template_name}"
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
            LOG.info(msg=f"get_templates_by_template timed out. {e}")
            return None

    def check_template(self, template_name, template_version):
        get_url = f"{self.RE_BACKEND_URL}{self.TEMPLATES_URL}/{template_name}/{template_version}"
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
            LOG.info(msg=f"check_template timed out. {e}")
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
        LOG.info(f"Get Volumes {volume_ids}")

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
                LOG.exception(f"Could not find volume {id}")

        return volumes

    def get_volume(self, volume_id):
        LOG.info(f"Get Volume {volume_id}")
        try:

            os_volume = self.conn.get_volume_by_id(id=volume_id)
            LOG.info(os_volume)
            if os_volume.attachments:
                device = os_volume.attachments[0]["device"]
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
            LOG.exception(f"Could not find volume {id}")
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
            LOG.exception(f"No Server  {openstack_id} ")
            raise serverNotFoundException(Reason=f"No Server {openstack_id}")

        LOG.info(f"Attaching volume {volume_id} to virtualmachine {openstack_id}")
        try:
            attachment = self.conn.compute.create_volume_attachment(
                server=server, volumeId=volume_id
            )
            return {"device": attachment["device"]}
        except ConflictException as e:
            LOG.exception(
                f"Trying to attach volume {volume_id} to vm {openstack_id} error : {e}",
                exc_info=True,
            )
            raise conflictException(Reason="409")
        except Exception as e:
            LOG.exception(
                f"Trying to attach volume {volume_id} to vm {openstack_id} error : {e}",
                exc_info=True,
            )
            return {"error": e}

    def check_server_status(self, openstack_id: str) -> VM:
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
        LOG.info(f"Check Status VM {openstack_id}")
        try:
            server = self.conn.compute.get_server(openstack_id)
        except Exception:
            LOG.exception(f"No Server with id  {openstack_id} ")
            return VM(status=self.NOT_FOUND)

        if server is None:
            LOG.exception(f"No Server with id {openstack_id} ")
            return VM(status=self.NOT_FOUND)

        serv = server.to_dict()

        try:
            if serv["status"] == self.ACTIVE:
                host = self.get_server(openstack_id).floating_ip
                port = self.SSH_PORT

                if self.USE_GATEWAY:
                    serv_cop = self.get_server(openstack_id)
                    server_base = serv_cop.fixed_ip.split(".")[-1]
                    ip_base = serv_cop.fixed_ip.split(".")[-2]
                    x = int(server_base)  # noqa F841
                    y = int(ip_base)  # noqa F841
                    host = str(self.GATEWAY_IP)
                    port = eval(self.SSH_FORMULAR)
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
            LOG.exception(f"Check Status VM {openstack_id} error: {e}")
            return VM(status=self.ERROR)

    def openstack_server_to_thrift_server(self, server: Server) -> VM:
        LOG.info(f"Convert server {server} to thrift server")
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
                LOG.exception(f"Could not found volume {volume_id}: {e}")
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
        task = server.task_state
        if task:
            status = task.upper().replace("-", "_")
            LOG.info(f"{server.id} Task: {task}")

        else:
            status = server.status
        server = VM(
            flav=flav,
            img=img,
            status=status,
            metadata=server.metadata,
            project_id=server.project_id,
            keyname=server.key_name,
            openstack_id=server.id,
            name=server.name,
            created_at=server.created_at,
            fixed_ip=fixed_ip,
            floating_ip=floating_ip,
            diskspace=diskspace,
        )
        return server

    def get_servers(self):
        LOG.info("Get all servers")
        servers = self.conn.list_servers()
        LOG.info(f"Found {len(servers)} servers")
        server_list = []
        for server in servers:
            try:
                thrift_server = self.openstack_server_to_thrift_server(server)
                server_list.append(thrift_server)

            except Exception as e:
                LOG.exception(f"Could not transform to thrift_server: {e}")
        LOG.info(f"Converted {len(server_list)} servers to thrift_server objects")
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
        LOG.info(f"Setting up UDP security group for {server_id}")
        server = self.conn.get_server(name_or_id=server_id)
        if server is None:
            LOG.exception(f"Instance {server_id} not found")
            raise serverNotFoundException
        sec = self.conn.get_security_group(name_or_id=server.name + "_udp")
        if sec:
            LOG.info(
                f"UDP Security group with name {server.name + '_udp'} already exists."
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

        server = self.get_server(server_id)
        server_base = server.fixed_ip.split(".")[-1]
        ip_base = server.fixed_ip.split(".")[-2]
        x = int(server_base)  # noqa F841
        y = int(ip_base)  # noqa F841
        udp_port = eval(self.UDP_FORMULAR)
        security_group = self.create_security_group(
            name=server.name + "_udp",
            udp_port=udp_port,
            udp=True,
            ssh=False,
            https=False,
            http=False,
            description="UDP",
        )
        LOG.info(security_group)
        LOG.info(f"Add security group {security_group.id} to server {server_id} ")
        self.conn.compute.add_security_group_to_server(
            server=server_id, security_group=security_group
        )

        return True

    def add_server_metadata(self, server_id, metadata) -> None:
        LOG.info(f"Add metadata - {metadata} to server - {server_id}")
        server = self.conn.get_server(name_or_id=server_id)
        if server is None:
            LOG.exception(f"Instance {server_id} not found")
            raise serverNotFoundException
        existing_metadata: Dict[string, any] = server.metadata
        if not existing_metadata:
            existing_metadata = {}
        existing_metadata.update(metadata)
        self.conn.set_server_metadata(server_id, metadata)

    def detach_ip_from_server(self, server_id, floating_ip):
        LOG.info(f"Detaching floating ip {floating_ip} from server {server_id}")
        try:
            self.conn.compute.remove_floating_ip_from_server(
                server=server_id, address=floating_ip
            )
            return True
        except Exception:
            LOG.exception(
                f"Could not detach floating ip {floating_ip} from server {server_id}"
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
        LOG.info(f"Get IP and PORT for server {openstack_id}")
        server = self.get_server(openstack_id)
        server_base = server.fixed_ip.split(".")[-1]
        ip_base = server.fixed_ip.split(".")[-2]
        x = int(server_base)  # noqa F841
        y = int(ip_base)  # noqa F841
        port = eval(self.SSH_FORMULAR)
        udp_port = eval(self.UDP_FORMULAR)
        return {"port": str(port), "udp": str(udp_port)}

    def terminate_cluster(self, cluster_id):
        headers = {"content-Type": "application/json"}
        body = {"mode": "openstack"}
        response = req.delete(
            url=f"{self.BIBIGRID_URL}terminate/{cluster_id}",
            json=body,
            headers=headers,
            verify=self.PRODUCTION,
        )
        LOG.info(response.json())
        return response.json()

    def get_cluster_status(self, cluster_id):
        LOG.info(f"Get Cluster {cluster_id} status")
        headers = {"content-Type": "application/json"}
        body = {"mode": "openstack"}
        request_url = self.BIBIGRID_URL + "info/" + cluster_id
        response = req.get(
            url=request_url, json=body, headers=headers, verify=self.PRODUCTION
        )
        json_resp = response.json(strict=False)
        json_resp["log"] = str(json_resp.get("log", ""))
        json_resp["msg"] = str(json_resp.get("msg", ""))
        msg = json_resp["msg"]
        info = json_resp.get("info", "")
        LOG.info(f"Cluster {cluster_id} status: - {msg} | {info}")
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

    def get_active_image_by_os_version(self, os_version, os_distro):
        LOG.info(f"Get active Image by os-version: {os_version}")
        images = self.conn.list_images()
        for image in images:
            if image and image.status == "active":
                image_os_version = image.get("os_version", None)
                image_os_distro = image.get("os_distro", None)
                properties = image.get("properties", None)
                base_image_ref = None
                if properties:
                    base_image_ref = properties.get("base_image_ref", None)
                if os_version == image_os_version and base_image_ref is None:
                    if os_distro and os_distro == image_os_distro:
                        return image
                    elif os_distro is None:

                        return image
        return None

    def create_deactivate_update_script(self):
        fileDir = os.path.dirname(os.path.abspath(__file__))
        deactivate_update_script_file = os.path.join(fileDir, "scripts/bash/mount.sh")
        with open(deactivate_update_script_file, "r") as file:
            deactivate_update_script = file.read()
            deactivate_update_script = encodeutils.safe_encode(
                deactivate_update_script.encode("utf-8")
            )
        return deactivate_update_script

    def add_cluster_machine(
        self,
        cluster_id,
        cluster_user,
        cluster_group_id,
        image,
        flavor,
        name,
        key_name,
        batch_idx,
        worker_idx,
        pub_key,
        project_name,
        project_id,
    ):
        LOG.info(
            f"Add machine to [{name}] {cluster_id} - [Image: {image}] - {key_name}"
        )
        try:
            openstack_image = self.get_image(image=image)
        except imageNotFoundException:
            openstack_image = None
            for version in ["18.04", "20.04", "22.04", "1804", "2004", "2204"]:
                LOG.info(f"Checking if [{version}] in [{image}]")

                if version in image:
                    LOG.info(f"Version {version} in {image}!\Checking for image ...")
                    openstack_image = self.get_active_image_by_os_version(
                        os_version=version, os_distro="ubuntu"
                    )
                    break
            if not openstack_image:
                raise imageNotFoundException(Reason=(f"No Image {image} found!"))

        if openstack_image and openstack_image.status != "active":
            LOG.info(openstack_image)
            image_os_version = openstack_image.get("os_version", "ubuntu")
            image_os_distro = openstack_image.get("os_distro", "1804")
            openstack_image = self.get_active_image_by_os_version(
                os_version=image_os_version, os_distro=image_os_distro
            )
            if not openstack_image:
                raise imageNotFoundException(
                    Reason=(
                        f"No active Image with os_version {image_os_version} found!"
                    )
                )
        flavor = self.get_flavor(flavor=flavor)
        network = self.get_network()
        metadata = {
            "bibigrid-id": cluster_id,
            "user": cluster_user or "",
            "worker-batch": str(batch_idx),
            "name": name or "",
            "worker-index": str(worker_idx),
            "project_name": project_name,
            "project_id": project_id,
        }

        new_key_name = f"{str(uuid4())[0:10]}".replace("-", "")

        self.conn.compute.create_keypair(name=new_key_name, public_key=pub_key)

        server = self.conn.create_server(
            name=name,
            image=openstack_image.id,
            flavor=flavor.id,
            network=[network.id],
            userdata=self.BIBIGRID_DEACTIVATE_UPRADES_SCRIPT,
            key_name=new_key_name,
            meta=metadata,
            availability_zone=self.AVAIALABILITY_ZONE,
            security_groups=cluster_group_id,
        )
        LOG.info(f"Created cluster machine:{server['id']}")

        self.delete_keypair(new_key_name)

        return server["id"]

    def get_cluster_info(self, cluster_id):
        infos = self.get_clusters_info()
        for info in infos:
            LOG.info(cluster_id)
            LOG.info(info)
            LOG.info(info["cluster-id"])
            LOG.info(cluster_id == info["cluster-id"])
            if info["cluster-id"] == cluster_id:
                pub_key = self.conn.compute.find_keypair(info["key name"])
                if pub_key:
                    pub_key = pub_key.public_key
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
                    pub_key=pub_key,
                )
                LOG.info(f"CLuster info : {cluster_info}")
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
            "ansibleGalaxyRoles": self.BIBIGRID_ANSIBLE_ROLES,
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

        server = self.conn.get_server_by_id(openstack_id)
        LOG.info(server)
        if server is None:
            LOG.exception(f"Instance {openstack_id} not found")
            raise serverNotFoundException
        try:
            snapshot_munch = self.conn.create_image_snapshot(server=server, name=name)
        except ConflictException as e:
            LOG.exception(f"Create snapshot {openstack_id} error: {e}")

            raise conflictException(Reason="409")
        except Exception:
            LOG.exception(f"Instance {openstack_id} not found")
            return None
        try:
            snapshot = self.conn.get_image_by_id(snapshot_munch["id"])
            snapshot_id = snapshot["id"]
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
                return None
            try:
                self.conn.image.add_tag(image=snapshot_id, tag=elixir_id)
            except Exception:
                LOG.exception(
                    f"Could not add Tag {elixir_id} to Snapshot: {snapshot_id}"
                )
                return None

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
        LOG.info(f"Delete Image {image_id}")
        try:
            image = self.conn.compute.get_image(image_id)
            if image is None:
                LOG.exception(f"Image {image} not found!")
                raise imageNotFoundException(Reason=f"Image {image} not found")
            self.conn.compute.delete_image(image)
            return True
        except Exception as e:
            LOG.exception(f"Delete Image {image_id} error : {e}")
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
                LOG.exception(f"Instance {openstack_id} not found")
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
                f"Adding Floating IP to {openstack_id} with network {network} error:{e}"
            )
            return None

    def netcat(self, host, port):
        """
        Try to connect to specific host:port.

        :param host: Host to connect
        :param port: Port to connect
        :return: True if successfully connected, False if not
        """
        LOG.info(f"Checking SSH Connection {host}:{port}")
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            r = sock.connect_ex((host, port))
            LOG.info(f"Checking SSH Connection {host}:{port} Result = {r}")
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
                    LOG.error(f"Instance {openstack_id} not found")
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
                if sec["name"] != self.DEFAULT_SECURITY_GROUP_NAME
                and "bibigrid" not in sec["name"]
            ]
            if security_groups is not None:
                for sg in security_groups:
                    LOG.info(f"Delete security group {sg['name']}")
                    self.conn.compute.remove_security_group_from_server(
                        server=server, security_group=sg
                    )
                    self.conn.network.delete_security_group(sg)
                self.conn.compute.delete_server(server)
            else:
                return False

            return True
        except ConflictException as e:
            LOG.exception(f"Delete Server {openstack_id} error: {e}")

            raise conflictException(Reason="409")
        except Exception as e:
            LOG.exception(f"Delete Server {openstack_id} error: {e}")
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
                    LOG.info(f"Delete Volume Attachment  {volume_attachment_id}")
                    self.conn.compute.delete_volume_attachment(
                        volume_attachment=volume_attachment_id, server=server_id
                    )
            return True
        except ConflictException:
            LOG.exception(
                f"Delete volume attachment (server: {server_id} volume: {volume_id}) error"
            )

            raise conflictException(Reason="409")
        except Exception:
            LOG.exception(f"Delete Volume Attachment  {volume_attachment_id} error")
            return False

    def delete_volume(self, volume_id):
        """
        Delete volume.

        :param volume_id: Id of the volume
        :return: True if deleted, False if not
        """

        try:
            LOG.info(f"Delete Volume  {volume_id}")
            self.conn.block_storage.delete_volume(volume=volume_id)
            return True
        except ConflictException:
            LOG.exception(f"Delete volume {volume_id} error")

            raise conflictException(Reason="409")
        except Exception:
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
        except ConflictException:
            LOG.exception(f"Stop Server {openstack_id} error")

            raise conflictException(Reason="409")
        except Exception:
            LOG.exception(f"Stop Server {openstack_id} error:")

            return False

    def reboot_server(self, server_id, reboot_type):
        """
        Reboot server.

        :param server_id: Id of the server
        :param reboot_type: HARD or SOFT
        :return:  True if resumed, False if not
        """
        LOG.info(f"Reboot Server {server_id} {reboot_type}")
        try:
            server = self.conn.compute.get_server(server_id)
            if server is None:
                LOG.exception(f"Instance {server_id} not found")
                raise serverNotFoundException
            else:
                self.conn.compute.reboot_server(server, reboot_type)
                return True
        except ConflictException:
            LOG.exception(f"Reboot Server {server_id} error")

            raise conflictException(Reason="409")
        except Exception:
            LOG.exception(f"Reboot Server {server_id} {reboot_type} Error")
            return False

    def resume_server(self, openstack_id):
        """
        Resume stopped server.

        :param openstack_id: Id of the server.
        :return: True if resumed, False if not
        """
        LOG.info(f"Resume Server {openstack_id}")
        try:
            server = self.conn.compute.get_server(openstack_id)
            if server is None:
                LOG.exception(f"Instance {openstack_id} not found")
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

    def validate_gateway_security_group(self):
        LOG.info(
            f"Check if gateway security group exists {self.GATEWAY_SECURITY_GROUP_ID}"
        )
        gateway_security_id = self.conn.get_security_group(
            self.GATEWAY_SECURITY_GROUP_ID
        )
        if not gateway_security_id:
            LOG.error(
                f"Gateway Security Group ID {self.GATEWAY_SECURITY_GROUP_ID} does not exist!"
            )
            sys.exit(1)
        else:
            LOG.info(
                f"Gateway Security Group ID {self.GATEWAY_SECURITY_GROUP_ID} found"
            )

    def create_or_get_default_ssh_security_group(self):
        LOG.info("Get default SimpleVM SSH Security Group")
        sec = self.conn.get_security_group(name_or_id=self.DEFAULT_SECURITY_GROUP_NAME)
        if not sec:
            LOG.info("Default SimpleVM SSH Security group not found... Creating")

            self.create_security_group(
                name=self.DEFAULT_SECURITY_GROUP_NAME,
                ssh=True,
                description="Default SSH SimpleVM Security Group",
            )

    def create_security_group(
        self,
        name,
        udp_port=None,
        ssh=True,
        http=False,
        https=False,
        udp=False,
        description=None,
        resenv=[],
    ):
        LOG.info(f"Create new security group {name}")
        sec = self.conn.get_security_group(name_or_id=name)
        if sec:
            LOG.info(f"Security group with name {name} already exists.")
            return sec
        new_security_group = self.conn.create_security_group(
            name=name, description=description
        )
        LOG.info(new_security_group)
        if http:
            LOG.info(f"Add http rule to security group {name}")
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
            LOG.info(f"Add https rule to security group {name}")

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
                "Add udp rule port {} to security group {} ({})".format(
                    udp_port,
                    name,
                    new_security_group["id"],
                )
            )

            self.conn.network.create_security_group_rule(
                direction="ingress",
                protocol="udp",
                port_range_max=udp_port,
                port_range_min=udp_port,
                security_group_id=new_security_group["id"],
                remote_group_id=self.GATEWAY_SECURITY_GROUP_ID,
            )
            self.conn.network.create_security_group_rule(
                direction="ingress",
                ether_type="IPv6",
                protocol="udp",
                port_range_max=udp_port,
                port_range_min=udp_port,
                security_group_id=new_security_group["id"],
                remote_group_id=self.GATEWAY_SECURITY_GROUP_ID,
            )
        if ssh:
            LOG.info(f"Add ssh rule to security group {name}")

            self.conn.network.create_security_group_rule(
                direction="ingress",
                protocol="tcp",
                port_range_max=22,
                port_range_min=22,
                security_group_id=new_security_group["id"],
                remote_group_id=self.GATEWAY_SECURITY_GROUP_ID,
            )
            self.conn.network.create_security_group_rule(
                direction="ingress",
                ether_type="IPv6",
                protocol="tcp",
                port_range_max=22,
                port_range_min=22,
                security_group_id=new_security_group["id"],
                remote_group_id=self.GATEWAY_SECURITY_GROUP_ID,
            )
        for research_enviroment in resenv:
            if research_enviroment in self.loaded_resenv_metadata:
                LOG.info(
                    "Add " + research_enviroment + f" rule to security group {name}"
                )
                resenv_metadata = self.loaded_resenv_metadata[research_enviroment]
                self.conn.network.create_security_group_rule(
                    direction=resenv_metadata.direction,
                    protocol=resenv_metadata.protocol,
                    port_range_max=resenv_metadata.port,
                    port_range_min=resenv_metadata.port,
                    security_group_id=new_security_group["id"],
                    remote_group_id=self.FORC_REMOTE_ID,
                )
            # as MOSH is persisted as "optional" in resenv

            elif research_enviroment not in ["user_key_url", "optional"]:
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
        limits = {}
        limits.update(self.conn.get_compute_limits())
        limits.update(self.conn.get_volume_limits()["absolute"])

        return {
            "max_total_cores": str(limits["max_total_cores"]),
            "max_total_instances": str(limits["max_total_instances"]),
            "max_total_ram_size": str(math.ceil(limits["max_total_ram_size"] / 1024)),
            "total_cores_used": str(limits["total_cores_used"]),
            "total_instances_used": str(limits["total_instances_used"]),
            "total_ram_used": str(math.ceil(limits["total_ram_used"] / 1024)),
            "maxTotalVolumes": str(limits["maxTotalVolumes"]),
            "maxTotalVolumeGigabytes": str(limits["maxTotalVolumeGigabytes"]),
            "totalVolumesUsed": str(limits["totalVolumesUsed"]),
            "totalGigabytesUsed": str(limits["totalGigabytesUsed"]),
        }

    def install_ansible_galaxy_requirements(self):
        LOG.info("Installing Ansible galaxy requirements..")
        stream = os.popen(
            f"ansible-galaxy install -r {PLAYBOOKS_DIR}/packer/requirements.yml"
        )
        output = stream.read()
        LOG.info(output)

    def update_playbooks(self):
        if self.GITHUB_PLAYBOOKS_REPO is None:
            LOG.info(
                "Github playbooks repo url is None. Aborting download of playbooks."
            )
            return
        LOG.info(f"STARTED update of playbooks from - {self.GITHUB_PLAYBOOKS_REPO}")
        r = req.get(self.GITHUB_PLAYBOOKS_REPO)
        filename = "resenv_repo"
        with open(filename, "wb") as output_file:
            output_file.write(r.content)
        LOG.info("Downloading Completed")
        with zipfile.ZipFile(filename, "r") as zip_ref:
            zip_ref.extractall(PLAYBOOKS_DIR)

        resenvs_unziped_dir = next(
            filter(
                lambda f: os.path.isdir(f) and "resenvs" in f,
                glob.glob(PLAYBOOKS_DIR + "*"),
            )
        )
        shutil.copytree(resenvs_unziped_dir, PLAYBOOKS_DIR, dirs_exist_ok=True)
        shutil.rmtree(resenvs_unziped_dir, ignore_errors=True)
        self.ALL_TEMPLATES = [
            name
            for name in os.listdir(PLAYBOOKS_DIR)
            if name not in ["optional", "packer", ".github", "cluster"]
            and os.path.isdir(os.path.join(PLAYBOOKS_DIR, name))
        ]
        LOG.info(self.ALL_TEMPLATES)

        templates_metadata = self.load_resenv_metadata()
        for template_metadata in templates_metadata:
            try:
                if template_metadata.get(NEEDS_FORC_SUPPORT, False):
                    metadata = ResenvMetadata(
                        template_metadata[TEMPLATE_NAME],
                        template_metadata[PORT],
                        template_metadata[SECURITYGROUP_NAME],
                        template_metadata[SECURITYGROUP_DESCRIPTION],
                        template_metadata[SECURITYGROUP_SSH],
                        template_metadata[DIRECTION],
                        template_metadata[PROTOCOL],
                        template_metadata[INFORMATION_FOR_DISPLAY],
                        needs_forc_support=template_metadata.get(
                            NEEDS_FORC_SUPPORT, False
                        ),
                        json_string=json.dumps(template_metadata),
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
        self.install_ansible_galaxy_requirements()
        LOG.info(self.loaded_resenv_metadata)

    def load_resenv_metadata(self):
        templates_metada = []
        for template in self.ALL_TEMPLATES:
            try:
                with open(
                    f"{PLAYBOOKS_DIR}{template}/{template}_metadata.yml"
                ) as template_metadata:
                    try:
                        loaded_metadata = yaml.load(
                            template_metadata, Loader=yaml.FullLoader
                        )

                        templates_metada.append(loaded_metadata)

                    except Exception as e:
                        LOG.exception(
                            "Failed to parse Metadata yml: "
                            + template_metadata
                            + "\n"
                            + str(e)
                        )
            except Exception as e:
                LOG.exception(f"No Metadatafile found for {template} - {e}")
        return templates_metada

    def update_forc_allowed(self, template_metadata):
        if template_metadata["needs_forc_support"]:
            name = template_metadata[TEMPLATE_NAME]
            allowed_versions = []
            for forc_version in template_metadata[FORC_VERSIONS]:
                get_url = (
                    f"{self.RE_BACKEND_URL}{self.TEMPLATES_URL}/{name}/{forc_version}"
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
                    LOG.info(msg=f"checking template/version timed out. {e}")
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
        needs_forc_support,
        json_string,
    ):
        self.name = name
        self.port = port
        self.security_group_name = security_group_name
        self.security_group_description = security_group_description
        self.security_group_ssh = security_group_ssh
        self.direction = direction
        self.protocol = protocol
        self.information_for_display = information_for_display
        self.json_string = json_string
        self.needs_forc_support = needs_forc_support
