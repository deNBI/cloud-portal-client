from __future__ import annotations

import math
import os
import socket
import urllib
import urllib.parse
from contextlib import closing

import yaml
from forc_connector.template.template import ResearchEnvironmentMetadata
from openstack import connection
from openstack.block_storage.v3.volume import Volume
from openstack.compute.v2.flavor import Flavor
from openstack.compute.v2.image import Image
from openstack.compute.v2.keypair import Keypair
from openstack.compute.v2.server import Server
from openstack.exceptions import (
    ConflictException,
    OpenStackCloudException,
    ResourceFailure,
    ResourceNotFound,
)
from openstack.network.v2.network import Network
from openstack.network.v2.security_group import SecurityGroup
from oslo_utils import encodeutils
from ttypes import (
    DefaultException,
    FlavorNotFoundException,
    ImageNotFoundException,
    OpenStackConflictException,
    ResourceNotAvailableException,
    ServerNotFoundException,
    VolumeNotFoundException,
)
from util.logger import setup_custom_logger
from util.state_enums import VmStates, VmTaskStates

logger = setup_custom_logger(__name__)

BIOCONDA = "bioconda"

ALL_TEMPLATES = [BIOCONDA]


class OpenStackConnector:
    def __init__(self, config_file: str):
        # Config FIle Data
        logger.info("Initializing OpenStack Connector")
        self.GATEWAY_IP: str = ""
        self.NETWORK: str = ""
        self.SUB_NETWORK: str = ""
        self.PRODUCTION: bool = True
        self.AVAILABILITY_ZONE: str = "default"
        self.CLOUD_SITE: str = ""
        self.BASE_GATEWAY_PORT: int = 30000
        self.SSH_MULTIPLICATION_PORT: int = 1
        self.UDP_MULTIPLICATION_PORT: int = 10
        self.DEFAULT_SECURITY_GROUP_NAME: str = ""
        self.DEFAULT_SECURITY_GROUPS: list[str] = []

        # Environment Data
        self.USERNAME: str = ""
        self.PASSWORD: str = ""
        self.PROJECT_NAME: str = ""
        self.PROJECT_ID: str = ""
        self.USER_DOMAIN_NAME: str = ""
        self.AUTH_URL: str = ""
        self.PROJECT_DOMAIN_ID: str = ""
        self.FORC_SECURITY_GROUP_ID: str = ""

        self.load_env_config()
        self.load_config_yml(config_file)

        try:
            logger.info("Connecting to Openstack..")
            self.openstack_connection = connection.Connection(
                username=self.USERNAME,
                password=self.PASSWORD,
                auth_url=self.AUTH_URL,
                project_name=self.PROJECT_NAME,
                user_domain_name=self.USER_DOMAIN_NAME,
                project_domain_id=self.PROJECT_DOMAIN_ID,
            )
            self.openstack_connection.authorize()
            logger.info("Connected to Openstack")
        except Exception:
            logger.error("Client failed authentication at Openstack!")
            raise ConnectionError("Client failed authentication at Openstack")

        self.DEACTIVATE_UPGRADES_SCRIPT = self.create_deactivate_update_script()

    def load_config_yml(self, config_file: str) -> None:
        logger.info(f"Load config file openstack config - {config_file}")
        with open(config_file, "r") as ymlfile:
            cfg = yaml.load(ymlfile, Loader=yaml.SafeLoader)

            self.GATEWAY_IP = cfg["openstack"]["gateway_ip"]
            self.NETWORK = cfg["openstack"]["network"]
            self.SUB_NETWORK = cfg["openstack"]["sub_network"]
            self.PRODUCTION = cfg["production"]
            self.AVAILABILITY_ZONE = cfg["openstack"]["availability_zone"]
            self.CLOUD_SITE = cfg["openstack"]["cloud_site"]
            self.BASE_GATEWAY_PORT = cfg["openstack"]["base_gateway_port"]
            self.SSH_MULTIPLICATION_PORT = cfg["openstack"]["ssh_multiplication_port"]
            self.UDP_MULTIPLICATION_PORT = cfg["openstack"]["udp_multiplication_port"]
            self.FORC_SECURITY_GROUP_ID = cfg["forc"]["forc_security_group_id"]
            self.DEFAULT_SECURITY_GROUP_NAME = cfg["openstack"][
                "default_simple_vm_security_group_name"
            ]
            self.DEFAULT_SECURITY_GROUPS = [self.DEFAULT_SECURITY_GROUP_NAME]

    def load_env_config(self) -> None:
        logger.info("Load environment config: OpenStack")
        self.USERNAME = os.environ["OS_USERNAME"]
        self.PASSWORD = os.environ["OS_PASSWORD"]
        self.PROJECT_NAME = os.environ["OS_PROJECT_NAME"]
        self.PROJECT_ID = os.environ["OS_PROJECT_ID"]
        self.USER_DOMAIN_NAME = os.environ["OS_USER_DOMAIN_NAME"]
        self.AUTH_URL = os.environ["OS_AUTH_URL"]
        self.PROJECT_DOMAIN_ID = os.environ["OS_PROJECT_DOMAIN_ID"]

    def create_server(
        self,
        name: str,
        image_id: str,
        flavor_id: str,
        network_id: str,
        userdata: str,
        key_name: str,
        metadata: dict[str, str],
        security_groups: list[str],
    ) -> Server:
        logger.info(
            f"Create Server:\n\tname: {name}\n\timage_id:{image_id}\n\tflavor_id:{flavor_id}\n\tmetadata:{metadata}"
        )
        server: Server = self.openstack_connection.create_server(
            name=name,
            image=image_id,
            flavor=flavor_id,
            network=[network_id],
            userdata=userdata,
            key_name=key_name,
            meta=metadata,
            availability_zone=self.AVAILABILITY_ZONE,
            security_groups=security_groups,
        )
        return server

    def get_volume(self, name_or_id: str) -> Volume:
        logger.info(f"Get Volume {name_or_id}")
        volume: Volume = self.openstack_connection.get_volume(name_or_id=name_or_id)
        if volume is None:
            logger.exception(f"No Volume with id  {name_or_id} ")
            raise VolumeNotFoundException(
                message=f"No Volume with id  {name_or_id} ", name_or_id=name_or_id
            )
        return volume

    def delete_volume(self, volume_id: str) -> None:

        try:
            logger.info(f"Delete Volume   {volume_id} ")
            self.openstack_connection.delete_volume(name_or_id=volume_id)
        except ResourceNotFound as e:
            raise VolumeNotFoundException(message=e.message, name_or_id=volume_id)

        except ConflictException as e:
            logger.exception(f"Delete volume: {volume_id}) failed!")
            raise OpenStackCloudException(message=e.message)
        except OpenStackCloudException as e:
            raise DefaultException(message=e.message)

    def get_servers(self) -> list[Server]:
        logger.info("Get servers")
        servers: list[Server] = self.openstack_connection.list_servers()
        return servers

    def get_servers_by_ids(self, ids: list[str]) -> list[Server]:
        logger.info(f"Get Servers by IDS : {ids}")
        servers: list[Server] = []
        for server_id in ids:
            logger.info(f"Get server {server_id}")
            try:
                server = self.openstack_connection.get_server_by_id(server_id)
                servers.append(server)
            except Exception as e:
                logger.exception(f"Requested VM {server_id} not found!\n {e}")

        return servers

    def attach_volume_to_server(
        self, openstack_id: str, volume_id: str
    ) -> dict[str, str]:

        server = self.get_server(openstack_id=openstack_id)
        volume = self.get_volume(name_or_id=volume_id)

        logger.info(f"Attaching volume {volume_id} to virtualmachine {openstack_id}")
        try:
            attachment = self.openstack_connection.attach_volume(
                server=server, volume=volume
            )
            return {"device": attachment["device"]}
        except ConflictException as e:
            logger.exception(
                f"Trying to attach volume {volume_id} to vm {openstack_id} error failed!",
                exc_info=True,
            )
            raise OpenStackConflictException(message=e.message)

    def detach_volume(self, volume_id: str, server_id: str) -> None:

        try:

            logger.info(f"Delete Volume Attachment  {volume_id} - {server_id}")
            volume = self.get_volume(name_or_id=volume_id)
            server = self.get_server(openstack_id=server_id)
            self.openstack_connection.detach_volume(volume=volume, server=server)
        except ConflictException as e:
            logger.exception(
                f"Delete volume attachment (server: {server_id} volume: {volume_id}) failed!"
            )
            raise OpenStackConflictException(message=e.message)

    def resize_volume(self, volume_id: str, size: int) -> None:

        try:
            logger.info(f"Extend volume {volume_id} to size {size}")
            self.openstack_connection.block_storage.extend_volume(volume_id, size)
        except ResourceNotFound as e:
            raise VolumeNotFoundException(message=e.message, name_or_id=volume_id)
        except OpenStackCloudException as e:
            logger.exception(f"Could not extend volume {volume_id}")
            raise DefaultException(message=str(e))

    def create_volume(
        self, volume_name: str, volume_storage: int, metadata: dict[str, str]
    ) -> Volume:

        logger.info(f"Creating volume with {volume_storage} GB storage")
        try:
            volume: Volume = self.openstack_connection.block_storage.create_volume(
                name=volume_name, size=volume_storage, metadata=metadata
            )
            return volume
        except ResourceFailure as e:
            logger.exception(
                f"Trying to create volume with {volume_storage} GB  failed",
                exc_info=True,
            )
            raise ResourceNotAvailableException(message=e.message)

    def get_network(self) -> Network:

        network: Network = self.openstack_connection.network.find_network(self.NETWORK)
        if network is None:
            logger.exception(f"Network {network} not found!")
            raise Exception(f"Network {network} not found!")
        return network

    def import_keypair(self, keyname: str, public_key: str) -> dict[str, str]:
        logger.info(f"Get Keypair {keyname}")
        keypair: dict[str, str] = self.openstack_connection.get_keypair(
            name_or_id=keyname
        )
        if not keypair:
            logger.info(f"Create Keypair {keyname}")

            new_keypair: dict[str, str] = self.openstack_connection.create_keypair(
                name=keyname, public_key=public_key
            )
            return new_keypair

        elif keypair["public_key"] != public_key:
            logger.info(f"Key {keyname} has changed. Replace old Key")
            self.delete_keypair(key_name=keyname)
            old_keypair: dict[str, str] = self.openstack_connection.create_keypair(
                name=keyname, public_key=public_key
            )
            return old_keypair
        else:
            return keypair

    def delete_keypair(self, key_name: str) -> None:
        logger.info(f"Delete keypair: {key_name}")

        key_pair = self.openstack_connection.compute.find_keypair(key_name)
        if key_pair:
            self.openstack_connection.delete_keypair(name=key_name)

    def create_add_keys_script(self, keys: list[str]) -> str:
        logger.info("create add key script")
        file_dir = os.path.dirname(os.path.abspath(__file__))
        key_script = os.path.join(
            file_dir, "openstack_connector/scripts/bash/add_keys_to_authorized.sh"
        )
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

    def netcat(self, host: str, port: int) -> bool:
        logger.info(f"Checking SSH Connection {host}:{port}")
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(5)
            r = sock.connect_ex((host, port))
            logger.info(f"Checking SSH Connection {host}:{port} Result = {r}")
        return r == 0

    def get_flavor(self, name_or_id: str) -> Flavor:
        logger.info(f"Get flavor {name_or_id}")

        flavor: Flavor = self.openstack_connection.get_flavor(
            name_or_id=name_or_id, get_extra=True
        )
        if flavor is None:
            logger.exception(f"Flavor {name_or_id} not found!")
            raise FlavorNotFoundException(
                message=f"Flavor {name_or_id} not found!", name_or_id=name_or_id
            )
        return flavor

    def get_flavors(self) -> list[Flavor]:
        logger.info("Get Flavors")
        if self.openstack_connection:
            flavors: list[Flavor] = self.openstack_connection.list_flavors(
                get_extra=True
            )
            logger.info([flav["name"] for flav in flavors])
            return flavors
        else:
            logger.info("no connection")
            return []

    def get_servers_by_bibigrid_id(self, bibigrid_id: str) -> list[Server]:
        logger.info(f"Get Servery by Bibigrid id: {bibigrid_id}")
        filters = {"bibigrid_id": bibigrid_id, "name": bibigrid_id}
        servers: list[Server] = self.openstack_connection.list_servers(filters=filters)
        return servers

    def get_active_image_by_os_version(self, os_version: str, os_distro: str) -> Image:
        logger.info(f"Get active Image by os-version: {os_version}")
        images = self.openstack_connection.list_images()
        for img in images:
            image: Image = img
            metadata = image["metadata"]
            image_os_version = metadata.get("os_version", None)
            image_os_distro = metadata.get("os_distro", None)
            base_image_ref = metadata.get("base_image_ref", None)
            if (
                os_version == image_os_version
                and image.status == "active"
                and base_image_ref is None
            ):
                if os_distro and os_distro == image_os_distro:
                    return image
                elif os_distro is None:
                    return image
        raise ImageNotFoundException(
            message=f"Old Image was deactivated! No image with os_version:{os_version} and os_distro:{os_distro} found!",
            name_or_id="",
        )

    def get_image(self, name_or_id: str, replace_inactive: bool = False) -> Image:
        logger.info(f"Get Image {name_or_id}")

        image: Image = self.openstack_connection.get_image(name_or_id=name_or_id)
        if image is None:
            raise ImageNotFoundException(
                message=f"Image {name_or_id} not found!", name_or_id=name_or_id
            )
        if image and image.status != "active" and replace_inactive:
            metadata = image.get("metadata", None)
            image_os_version = metadata.get("os_version", None)
            image_os_distro = metadata.get("os_distro", None)
            image = self.get_active_image_by_os_version(
                os_version=image_os_version, os_distro=image_os_distro
            )
        elif image and image.status != "active":
            raise ImageNotFoundException(
                message=f"Image {name_or_id} found but not active!",
                name_or_id=name_or_id,
            )
        return image

    def create_snapshot(
        self,
        openstack_id: str,
        name: str,
        username: str,
        base_tags: list[str],
        description: str,
    ) -> str:

        logger.info(
            f"Create Snapshot from Instance {openstack_id} with name {name} for {username}"
        )

        try:
            snapshot_munch = self.openstack_connection.create_image_snapshot(
                server=openstack_id, name=name, description=description
            )
            for tag in base_tags:
                self.openstack_connection.image.add_tag(
                    image=snapshot_munch["id"], tag=tag
                )
            snapshot_id: str = snapshot_munch["id"]
            return snapshot_id

        except ConflictException as e:
            logger.exception(f"Create snapshot {openstack_id} failed!")

            raise OpenStackConflictException(message=e.message)
        except OpenStackCloudException as e:
            raise DefaultException(message=e.message)

    def delete_image(self, image_id: str) -> None:

        logger.info(f"Delete Image {image_id}")
        try:
            image = self.openstack_connection.get_image(image_id)
            if image is None:
                logger.exception(f"Image {image_id} not found!")
                raise ImageNotFoundException(
                    message=f"Image {image_id} not found!", name_or_id=image_id
                )
            self.openstack_connection.compute.delete_image(image)
        except Exception as e:
            logger.exception(f"Delete Image {image_id} failed!")
            raise DefaultException(message=str(e))

    def get_public_images(self) -> list[Image]:
        logger.info("Get public images")
        if self.openstack_connection:
            images = filter(
                lambda x: "tags" in x
                and len(x["tags"]) > 0
                and x["status"] == "active"
                and x["visibility"] == "public",
                self.openstack_connection.list_images(),
            )
            return list(images)

        else:
            logger.info("no connection")
            return []

    def get_private_images(self) -> list[Image]:
        logger.info("Get private images")
        if self.openstack_connection:
            images = filter(
                lambda x: "tags" in x
                and len(x["tags"]) > 0
                and x["status"] == "active"
                and x["visibility"] == "private",
                self.openstack_connection.list_images(),
            )
            return list(images)
        else:
            logger.info("no connection")
            return []

    def get_images(self) -> list[Image]:

        logger.info("Get Images")
        if self.openstack_connection:
            # todo check
            images = filter(
                lambda x: "tags" in x
                and len(x["tags"]) > 0
                and x["status"] == "active",
                self.openstack_connection.list_images(),
            )

            return list(images)
        else:
            logger.info("no connection")
            return []

    def get_calculation_values(self) -> dict[str, int]:
        logger.info("Get Client Calculation Values")
        return {
            "SSH_MULTIPLICATION_PORT": self.SSH_MULTIPLICATION_PORT,
            "UDP_MULTIPLICATION_PORT": self.UDP_MULTIPLICATION_PORT,
            "BASE_GATEWAY_PORT": self.BASE_GATEWAY_PORT,
        }

    def get_gateway_ip(self) -> dict[str, str]:
        logger.info("Get Gateway IP")

        return {"gateway_ip": self.GATEWAY_IP}

    def create_mount_init_script(
        self,
        new_volumes: list[dict[str, str]] = None,  # type: ignore
        attach_volumes: list[dict[str, str]] = None,  # type: ignore
    ) -> str:
        logger.info(f"Create init script for volume ids:{new_volumes}")
        if not new_volumes and not attach_volumes:
            return ""

        file_dir: str = os.path.dirname(os.path.abspath(__file__))
        mount_script: str = os.path.join(file_dir, "scripts/bash/mount.sh")

        if new_volumes:
            volume_ids_new = [vol["openstack_id"] for vol in new_volumes]
            paths_new = [vol["path"] for vol in new_volumes]
        else:
            volume_ids_new = []
            paths_new = []

        if attach_volumes:
            logger.info(attach_volumes)
            volume_ids_attach = [vol["openstack_id"] for vol in attach_volumes]
            paths_attach = [vol["path"] for vol in attach_volumes]
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
        return text

    def create_security_group(
        self,
        name: str,
        udp_port_start: int = None,  # type: ignore
        ssh: bool = True,
        udp: bool = False,
        description: str = "",
        research_environment_metadata: ResearchEnvironmentMetadata = None,
    ) -> SecurityGroup:
        logger.info(f"Create new security group {name}")
        sec: SecurityGroup = self.openstack_connection.get_security_group(
            name_or_id=name
        )
        if sec:
            logger.info(f"Security group with name {name} already exists.")
            return sec
        new_security_group: SecurityGroup = (
            self.openstack_connection.create_security_group(
                name=name, description=description
            )
        )

        if udp:
            logger.info(
                "Add udp rule ports {} - {} to security group {}".format(
                    udp_port_start, udp_port_start + 9, name
                )
            )

            self.openstack_connection.create_security_group_rule(
                direction="ingress",
                protocol="udp",
                port_range_max=udp_port_start + 9,
                port_range_min=udp_port_start,
                secgroup_name_or_id=new_security_group["id"],
            )
            self.openstack_connection.create_security_group_rule(
                direction="ingress",
                ethertype="IPv6",
                protocol="udp",
                port_range_max=udp_port_start + 9,
                port_range_min=udp_port_start,
                secgroup_name_or_id=new_security_group["id"],
            )
        if ssh:
            logger.info(f"Add ssh rule to security group {name}")

            self.openstack_connection.create_security_group_rule(
                direction="ingress",
                protocol="tcp",
                port_range_max=22,
                port_range_min=22,
                secgroup_name_or_id=new_security_group["id"],
            )
            self.openstack_connection.create_security_group_rule(
                direction="ingress",
                ethertype="IPv6",
                protocol="tcp",
                port_range_max=22,
                port_range_min=22,
                secgroup_name_or_id=new_security_group["id"],
            )
        if research_environment_metadata:
            self.openstack_connection.network.create_security_group_rule(
                direction=research_environment_metadata.direction,
                protocol=research_environment_metadata.protocol,
                port_range_max=research_environment_metadata.port,
                port_range_min=research_environment_metadata.port,
                security_group_id=new_security_group["id"],
                remote_group_id=self.FORC_SECURITY_GROUP_ID,
            )

        return new_security_group

    def prepare_security_groups_new_server(
        self,
        research_environment_metadata: ResearchEnvironmentMetadata,
        servername: str,
    ) -> list[str]:
        custom_security_groups = []

        if research_environment_metadata:
            custom_security_groups.append(
                self.create_security_group(
                    name=servername + research_environment_metadata.security_group_name,
                    ssh=research_environment_metadata.security_group_ssh,
                    description=research_environment_metadata.security_group_description,
                    research_environment_metadata=research_environment_metadata,
                ).name
            )

        return custom_security_groups

    def get_limits(self) -> dict[str, str]:

        logger.info("Get Limits")
        limits = self.openstack_connection.get_compute_limits()
        limits.update(self.openstack_connection.get_volume_limits()["absolute"])

        return {
            "cores_limit": str(limits["max_total_cores"]),
            "vms_limit": str(limits["max_total_instances"]),
            "ram_limit": str(math.ceil(limits["max_total_ram_size"] / 1024)),
            "current_used_cores": str(limits["total_cores_used"]),
            "current_used_vms": str(limits["total_instances_used"]),
            "current_used_ram": str(math.ceil(limits["total_ram_used"] / 1024)),
            "volume_counter_limit": str(limits["maxTotalVolumes"]),
            "volume_storage_limit": str(limits["maxTotalVolumeGigabytes"]),
            "current_used_volumes": str(limits["totalVolumesUsed"]),
            "current_used_volume_storage": str(limits["totalGigabytesUsed"]),
        }

    def exist_server(self, name: str) -> bool:

        if self.openstack_connection.compute.find_server(name) is not None:
            return True
        else:
            return False

    def get_server(self, openstack_id: str) -> Server:
        try:
            logger.info(f"Get Server by id: {openstack_id}")
            server: Server = self.openstack_connection.get_server_by_id(id=openstack_id)
            if server is None:
                logger.exception(f"Instance {openstack_id} not found")
                raise ServerNotFoundException(
                    message=f"Instance {openstack_id} not found",
                    name_or_id=openstack_id,
                )
            if server.status == VmStates.ACTIVE.value:
                server_base = int(server.private_v4.split(".")[-1])
                port = self.BASE_GATEWAY_PORT + (
                    server_base * self.SSH_MULTIPLICATION_PORT
                )

                if not self.netcat(host=self.GATEWAY_IP, port=port):
                    server.task_state = VmTaskStates.CHECKING_SSH_CONNECTION.value

            server.image = self.get_image(name_or_id=server.image["id"])

            server.flavor = self.get_flavor(name_or_id=server.flavor["id"])

            return server
        except OpenStackCloudException as e:
            raise DefaultException(
                message=f"Error when getting server {openstack_id}! - {e}"
            )

    def resume_server(self, openstack_id: str) -> None:

        logger.info(f"Resume Server {openstack_id}")
        try:
            server = self.get_server(openstack_id=openstack_id)
            if server is None:
                logger.exception(f"Instance {openstack_id} not found")
                raise ServerNotFoundException(
                    message=f"Instance {openstack_id} not found",
                    name_or_id=openstack_id,
                )
            self.openstack_connection.compute.start_server(server)

        except ConflictException as e:
            logger.exception(f"Resume Server {openstack_id} failed!")
            raise OpenStackConflictException(message=str(e))

    def reboot_hard_server(self, openstack_id: str) -> None:
        return self.reboot_server(openstack_id=openstack_id, reboot_type="HARD")

    def reboot_soft_server(self, openstack_id: str) -> None:
        return self.reboot_server(openstack_id=openstack_id, reboot_type="SOFT")

    def reboot_server(self, openstack_id: str, reboot_type: str) -> None:
        logger.info(f"Reboot Server {openstack_id} - {reboot_type}")
        server = self.get_server(openstack_id=openstack_id)
        try:
            self.openstack_connection.compute.reboot_server(server, reboot_type)
        except ConflictException as e:
            logger.exception(f"Reboot Server {openstack_id} failed!")

            raise OpenStackConflictException(message=str(e))

    def stop_server(self, openstack_id: str) -> None:

        logger.info(f"Stop Server {openstack_id}")
        server = self.get_server(openstack_id=openstack_id)
        try:
            if server is None:
                raise ServerNotFoundException(
                    message=f"Instance {openstack_id} not found",
                    name_or_id=openstack_id,
                )

            self.openstack_connection.compute.stop_server(server)

        except ConflictException as e:
            logger.exception(f"Stop Server {openstack_id} failed!")
            raise OpenStackConflictException(message=e.message)

    def delete_server(self, openstack_id: str) -> None:

        logger.info(f"Delete Server {openstack_id}")
        try:
            server = self.get_server(openstack_id=openstack_id)

            if not server:
                logger.error(f"Instance {openstack_id} not found")
                raise ServerNotFoundException(
                    message=f"Instance {openstack_id} not found",
                    name_or_id=openstack_id,
                )

            task_state = server.get("task_state", None)
            if (
                task_state == "image_snapshot"
                or task_state == "image_pending_upload"
                or task_state == "image_uploading"
            ):
                raise ConflictException("task_state in image creating")
            security_groups = server["security_groups"]
            security_groups = [
                sec
                for sec in security_groups
                if sec["name"] != self.DEFAULT_SECURITY_GROUP_NAME
                and "bibigrid" not in sec["name"]
            ]
            if security_groups is not None:
                for sg in security_groups:
                    logger.info(f"Delete security group {sg['name']}")
                    self.openstack_connection.compute.remove_security_group_from_server(
                        server=server, security_group=sg
                    )
                    self.openstack_connection.delete_security_group(sg)
            self.openstack_connection.delete_server(server)
        except ConflictException as e:
            logger.error(f"Delete Server {openstack_id} failed!")

            raise OpenStackConflictException(message=e.message)

    def get_vm_ports(self, openstack_id: str) -> dict[str, str]:
        logger.info(f"Get IP and PORT for server {openstack_id}")
        server = self.get_server(openstack_id=openstack_id)
        if not server:
            raise ServerNotFoundException(
                message=f"Server {openstack_id} not found!", name_or_id=openstack_id
            )
        server_base = int(server["private_v4"].split(".")[-1])
        ssh_port = (
            self.BASE_GATEWAY_PORT + int(server_base) * self.SSH_MULTIPLICATION_PORT
        )
        udp_port = (
            self.BASE_GATEWAY_PORT + int(server_base) * self.UDP_MULTIPLICATION_PORT
        )
        return {"port": str(ssh_port), "udp": str(udp_port)}

    def create_userdata(
        self,
        volume_ids_path_new: list[dict[str, str]],
        volume_ids_path_attach: list[dict[str, str]],
        additional_keys: list[str],
    ) -> str:

        init_script = self.create_mount_init_script(
            new_volumes=volume_ids_path_new,
            attach_volumes=volume_ids_path_attach,
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
        return init_script

    def start_server(
        self,
        flavor_name: str,
        image_name: str,
        servername: str,
        metadata: dict[str, str],
        public_key: str,
        research_environment_metadata: ResearchEnvironmentMetadata = None,
        volume_ids_path_new: list[dict[str, str]] = None,  # type: ignore
        volume_ids_path_attach: list[dict[str, str]] = None,  # type: ignore
        additional_keys: list[str] = None,  # type: ignore
    ) -> str:
        logger.info(f"Start Server {servername}")

        key_name: str = None  # type: ignore
        try:

            image: Image = self.get_image(name_or_id=image_name)
            flavor: Flavor = self.get_flavor(name_or_id=flavor_name)
            network: Network = self.get_network()
            key_name = f"{servername}_{metadata['project_name']}"
            logger.info(f"Key name {key_name}")
            custom_security_groups = self.prepare_security_groups_new_server(
                research_environment_metadata=research_environment_metadata,
                servername=servername,
            )
            public_key = urllib.parse.unquote(public_key)
            self.import_keypair(key_name, public_key)
            volume_ids = []
            volumes = []
            if volume_ids_path_new:
                volume_ids.extend([vol["openstack_id"] for vol in volume_ids_path_new])
            if volume_ids_path_attach:
                volume_ids.extend(
                    [vol["openstack_id"] for vol in volume_ids_path_attach]
                )
            logger.info(f"volume ids {volume_ids}")
            for volume_id in volume_ids:
                try:
                    volumes.append(self.get_volume(name_or_id=volume_id))
                except VolumeNotFoundException:
                    pass
            init_script = self.create_userdata(
                volume_ids_path_new=volume_ids_path_new,
                volume_ids_path_attach=volume_ids_path_attach,
                additional_keys=additional_keys,
            )
            logger.info(f"Starting Server {servername}...")
            server = self.openstack_connection.create_server(
                name=servername,
                image=image.id,
                flavor=flavor.id,
                network=[network.id],
                key_name=key_name,
                meta=metadata,
                volumes=volumes,
                userdata=init_script,
                availability_zone=self.AVAILABILITY_ZONE,
                security_groups=self.DEFAULT_SECURITY_GROUPS + custom_security_groups,
            )

            openstack_id: str = server["id"]
            self.delete_keypair(key_name=key_name)

            return openstack_id

        except OpenStackCloudException as e:
            if key_name:
                self.delete_keypair(key_name=key_name)

            for security_group in custom_security_groups:
                self.openstack_connection.delete_security_group(security_group)
            logger.exception(f"Start Server {servername} error:{e}")
            raise DefaultException(message=str(e))

    def start_server_with_playbook(
        self,
        flavor_name: str,
        image_name: str,
        servername: str,
        metadata: dict[str, str],
        research_environment_metadata: ResearchEnvironmentMetadata,
        volume_ids_path_new: list[dict[str, str]] = None,  # type: ignore
        volume_ids_path_attach: list[dict[str, str]] = None,  # type: ignore
        additional_keys: list[str] = None,  # type: ignore
    ) -> tuple[str, str]:
        logger.info(f"Start Server {servername}")
        custom_security_groups = self.prepare_security_groups_new_server(
            research_environment_metadata=research_environment_metadata,
            servername=servername,
        )
        key_name = ""
        try:

            image: Image = self.get_image(name_or_id=image_name)
            flavor: Flavor = self.get_flavor(name_or_id=flavor_name)
            network: Network = self.get_network()

            key_creation: Keypair = self.openstack_connection.create_keypair(
                name=servername
            )

            private_key = key_creation.private_key

            volume_ids = []
            volumes = []
            if volume_ids_path_new:
                volume_ids.extend([vol["openstack_id"] for vol in volume_ids_path_new])
            if volume_ids_path_attach:
                volume_ids.extend(
                    [vol["openstack_id"] for vol in volume_ids_path_attach]
                )
            logger.info(f"volume ids {volume_ids}")
            for volume_id in volume_ids:
                volumes.append(
                    self.openstack_connection.get_volume(name_or_id=volume_id)
                )
            init_script = self.create_userdata(
                volume_ids_path_new=volume_ids_path_new,
                volume_ids_path_attach=volume_ids_path_attach,
                additional_keys=additional_keys,
            )
            server = self.openstack_connection.create_server(
                name=servername,
                image=image.id,
                flavor=flavor.id,
                network=[network.id],
                key_name=servername,
                meta=metadata,
                volumes=volumes,
                userdata=init_script,
                availability_zone=self.AVAILABILITY_ZONE,
                security_groups=self.DEFAULT_SECURITY_GROUPS + custom_security_groups,
            )

            openstack_id = server["id"]
            self.delete_keypair(key_name=key_creation.name)

            return openstack_id, private_key

        except OpenStackCloudException as e:
            if key_name:
                self.delete_keypair(key_name=key_name)

            for security_group in custom_security_groups:
                self.openstack_connection.delete_security_group(security_group)
            logger.exception(f"Start Server {servername} error:{e}")
            raise DefaultException(message=str(e))

    def create_deactivate_update_script(self) -> str:
        file_dir = os.path.dirname(os.path.abspath(__file__))
        deactivate_update_script_file = os.path.join(file_dir, "scripts/bash/mount.sh")
        with open(deactivate_update_script_file, "r") as file:
            deactivate_update_script = file.read()
            deactivate_update_script = encodeutils.safe_encode(
                deactivate_update_script.encode("utf-8")
            )
        return deactivate_update_script

    def add_cluster_machine(
        self,
        cluster_id: str,
        cluster_user: str,
        cluster_group_id: list[str],
        image_name: str,
        flavor_name: str,
        name: str,
        key_name: str,
        batch_idx: int,
        worker_idx: int,
    ) -> str:
        logger.info(f"Add machine to {cluster_id}")
        image: Image = self.get_image(name_or_id=image_name, replace_inactive=True)
        flavor: Flavor = self.get_flavor(name_or_id=flavor_name)
        network = self.get_network()
        metadata = {
            "bibigrid-id": cluster_id,
            "user": cluster_user or "",
            "worker-batch": str(batch_idx),
            "name": name or "",
            "worker-index": str(worker_idx),
        }

        server = self.create_server(
            name=name,
            image_id=image.id,
            flavor_id=flavor.id,
            network_id=network.id,
            userdata=self.DEACTIVATE_UPGRADES_SCRIPT,
            key_name=key_name,
            metadata=metadata,
            security_groups=cluster_group_id,
        )
        logger.info(f"Created cluster machine:{server['id']}")
        server_id: str = server["id"]
        return server_id
