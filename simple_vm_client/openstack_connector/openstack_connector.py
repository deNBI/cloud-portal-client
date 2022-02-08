import os
import socket
import urllib
from contextlib import closing
from uuid import uuid4

import yaml
from openstack import connection
from openstack.exceptions import ConflictException, NotFoundException, ResourceFailure
from oslo_utils import encodeutils
from ttypes import imageNotFoundException
from util.logger import setup_custom_logger
from util.state_enums import VmStates

logger = setup_custom_logger(__name__)

BIOCONDA = "bioconda"

ALL_TEMPLATES = [BIOCONDA]


class OpenStackConnector:
    def __init__(self, config_file):
        # Config FIle Data
        logger.info("Initializing OpenStack Connector")
        self.GATEWAY_IP = None
        self.NETWORK = None
        self.SUB_NETWORK = None
        self.PRODUCTION = None
        self.AVAILABILITY_ZONE = "default"
        self.CLOUD_SITE = None
        self.BASE_GATEWAY_PORT = 30000
        self.SSH_MULTIPLICATION_PORT = 1
        self.UDP_MULTIPLICATION_PORT = 10
        self.DEFAULT_SECURITY_GROUP_NAME = None
        self.DEFAULT_SECURITY_GROUPS = []

        # Environment Data
        self.USERNAME = None
        self.PASSWORD = None
        self.PROJECT_NAME = None
        self.PROJECT_ID = None
        self.USER_DOMAIN_NAME = None
        self.AUTH_URL = None
        self.PROJECT_DOMAIN_ID = None
        self.FORC_SECURITY_GROUP_ID = None

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

    def load_config_yml(self, config_file):
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

    def load_env_config(self):
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
        name,
        image_id,
        flavor_id,
        network_id,
        userdata,
        key_name,
        metadata,
        security_groups,
    ):
        logger.info(
            f"Create Server:\n\tname: {name}\n\timage_id:{image_id}\n\tflavor_id:{flavor_id}\n\tmetadata:{metadata}"
        )
        return self.openstack_connection.create_server(
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

    def get_volume(self, name_or_id):
        logger.info(f"Get Volume {name_or_id}")
        volume = self.openstack_connection.get_volume(name_or_id=name_or_id)

        if volume is None:
            logger.exception(f"No Volume with id  {name_or_id} ")
            return {"status": VmStates.NOT_FOUND, "id": name_or_id}
        return volume

    def delete_volume(self, volume_id):

        try:
            logger.info(f"Delete Volume   {volume_id} ")
            volume = self.openstack_connection.get_volume(name_or_id=volume_id)

            if volume is None:
                logger.exception(f"No Volume with id  {volume_id} ")
                return False

            self.openstack_connection.delete_volume(name_or_id=volume_id)
            return True
        except ConflictException as e:
            logger.exception(f"Delete volume attachment (volume: {volume_id}) failed!")
            raise e

    def get_servers(self):
        logger.info("Get servers")
        servers = self.openstack_connection.list_servers()
        return servers

    def get_servers_by_ids(self, ids):
        logger.info(f"Get Servers by IDS : {ids}")
        servers = []
        for id in ids:
            logger.info(f"Get server {id}")
            try:
                server = self.openstack_connection.get_server_by_id(id)
                servers.append(server)
            except Exception as e:
                logger.exception("Requested VM {} not found!\n {}".format(id, e))

        return servers

    def attach_volume_to_server(self, openstack_id, volume_id):

        server = self.openstack_connection.get_server(name_or_id=openstack_id)

        if server is None:
            logger.exception("No Server {0} ".format(openstack_id))
            return {"error": "server not found"}

        logger.info(f"Attaching volume {volume_id} to virtualmachine {openstack_id}")
        try:
            attachment = self.openstack_connection.compute.create_volume_attachment(
                server=server, volumeId=volume_id
            )
            return {"device": attachment["device"]}
        except ConflictException as e:
            logger.exception(
                f"Trying to attach volume {volume_id} to vm {openstack_id} error failed!",
                exc_info=True,
            )
            return {"error": e}

    def detach_volume(self, volume_id, server_id):

        try:

            logger.info(f"Delete Volume Attachment  {volume_id} - {server_id}")
            volume = self.openstack_connection.get_volume(name_or_id=volume_id)

            if volume is None:
                logger.exception(f"No Volume with id  {volume_id} ")
                return False

            server = self.openstack_connection.get_server(name_or_id=server_id)
            if server is None:
                logger.exception(f"No Server with id  {server_id} ")
                return False

            self.openstack_connection.detach_volume(volume=volume, server=server)
            return True
        except ConflictException as e:
            logger.exception(
                f"Delete volume attachment (server: {server_id} volume: {volume_id}) failed!"
            )
            raise e

    def resize_volume(self, volume_id, size):

        try:
            logger.info(f"Extend volume {volume_id} to size {size}")
            self.openstack_connection.block_storage.extend_volume(volume_id, size)
        except Exception:
            logger.exception(f"Could not extend volume {volume_id}")
            return 1
        return 0

    def create_volume(self, volume_name, volume_storage, metadata):

        logger.info(f"Creating volume with {volume_storage} GB storage")
        try:
            volume = self.openstack_connection.block_storage.create_volume(
                name=volume_name, size=volume_storage, metadata=metadata
            )
            return volume
        except ResourceFailure as e:
            logger.exception(
                f"Trying to create volume with {volume_storage} GB  failed",
                exc_info=True,
            )
            raise e

    def get_network(self):

        network = self.openstack_connection.network.find_network(self.NETWORK)
        if network is None:
            logger.exception("Network {0} not found!".format(network))
            raise Exception("Network {0} not found!".format(network))
        return network

    def import_keypair(self, keyname, public_key):
        logger.info(f"Get Keypair {keyname}")
        keypair = self.openstack_connection.get_keypair(name_or_id=keyname)
        if not keypair:
            logger.info(f"Create Keypair {keyname}")

            keypair = self.openstack_connection.create_keypair(
                name=keyname, public_key=public_key
            )
            return {"keypair": keypair}

        elif keypair.public_key != public_key:
            logger.info(f"Key {keyname} has changed. Replace old Key")
            self.delete_keypair(key_name=keyname)
            keypair = self.openstack_connection.create_keypair(
                name=keyname, public_key=public_key
            )
            return keypair
        else:
            return keypair

    def delete_keypair(self, key_name):
        logger.info(f"Delete keypair: {key_name}")

        key_pair = self.openstack_connection.compute.find_keypair(key_name)
        if key_pair:
            self.openstack_connection.delete_keypair(name=key_name)

    def create_add_keys_script(self, keys):
        logger.info("create add key script")
        fileDir = os.path.dirname(os.path.abspath(__file__))
        key_script = os.path.join(
            fileDir, "openstack_connector/scripts/bash/add_keys_to_authorized.sh"
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

    def netcat(self, host, port):
        logger.info(f"Checking SSH Connection {host}:{port}")
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(5)
            r = sock.connect_ex((host, port))
            logger.info(f"Checking SSH Connection {host}:{port} Result = {r}")
        logger.info("Checking SSH Connection done!")
        return r == 0

    def get_flavor(self, name_or_id):
        logger.info(f"Get flavor {name_or_id}")

        flavor = self.openstack_connection.get_flavor(
            name_or_id=name_or_id, get_extra=True
        )
        if flavor is None:
            logger.exception(f"Flavor {name_or_id} not found!")
            raise Exception(f"Flavor {name_or_id} not found!")
        return flavor

    def get_flavors(self):
        logger.info("Get Flavors")
        if self.openstack_connection:
            flavors = self.openstack_connection.list_flavors(get_extra=True)
            logger.info([flav["name"] for flav in flavors])
            return flavors
        else:
            logger.info("no connection")
            return []

    def get_servers_by_bibigrid_id(self, bibigrid_id):
        logger.info(f"Get Servery by Bibigrid id: {bibigrid_id}")
        filters = {"bibigrid_id": bibigrid_id, "name": bibigrid_id}
        servers = self.openstack_connection.list_servers(filters=filters)
        return servers

    def get_active_image_by_os_version(self, os_version, os_distro):
        logger.info(f"Get active Image by os-version: {os_version}")
        images = self.openstack_connection.list_images()
        for image in images:
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
        return None

    def get_image(self, name_or_id, replace_inactive=False):
        logger.info(f"Get Image {name_or_id}")

        image = self.openstack_connection.get_image(name_or_id=name_or_id)
        if image is None:
            raise imageNotFoundException(Reason=(f"Image {name_or_id} not found!"))
        if image and image.status != "active" and replace_inactive:
            metadata = image.get("metadata", None)
            image_os_version = metadata.get("os_version", None)
            image_os_distro = metadata.get("os_distro", None)
            image = self.get_active_image_by_os_version(
                os_version=image_os_version, os_distro=image_os_distro
            )
        elif image and image.status != "active":
            raise imageNotFoundException(
                Reason=(f"Image {name_or_id} found but not active!")
            )
        return image

    def create_snapshot(self, openstack_id, name, elixir_id, base_tags, description):

        logger.info(
            f"Create Snapshot from Instance {openstack_id} with name {name} for {elixir_id}"
        )

        try:
            snapshot_munch = self.openstack_connection.create_image_snapshot(
                server=openstack_id, name=name, description=description
            )
            for tag in base_tags:
                self.openstack_connection.image.add_tag(
                    image=snapshot_munch["id"], tag=tag
                )
            return snapshot_munch["id"]

        except ConflictException as e:
            logger.exception(f"Create snapshot {openstack_id} failed!")

            raise e

    def delete_image(self, image_id):

        logger.info(f"Delete Image {image_id}")
        try:
            image = self.openstack_connection.compute.get_image(image_id)
            if image is None:
                logger.exception("Image {0} not found!".format(image))
                raise NotFoundException
            self.openstack_connection.compute.delete_image(image)
            return True
        except Exception:
            logger.exception(f"Delete Image {image_id} failed!")
            return False

    def get_public_images(self):
        logger.info("Get public images")
        if self.openstack_connection:
            images = filter(
                lambda x: "tags" in x
                and len(x["tags"]) > 0
                and x["status"] == "active"
                and x["visibility"] == "public",
                self.openstack_connection.list_images(),
            )
            return images

        else:
            logger.info("no connection")
            return []

    def get_private_images(self):
        logger.info("Get private images")
        if self.openstack_connection:
            images = filter(
                lambda x: "tags" in x
                and len(x["tags"]) > 0
                and x["status"] == "active"
                and x["visibility"] == "private",
                self.openstack_connection.list_images(),
            )
            return images
        else:
            logger.info("no connection")
            return []

    def get_images(self):

        logger.info("Get Images")
        if self.openstack_connection:
            # todo check
            images = filter(
                lambda x: "tags" in x
                and len(x["tags"]) > 0
                and x["status"] == "active",
                self.openstack_connection.list_images(),
            )

            return images
        else:
            logger.info("no connection")
            return []

    def get_calculation_values(self):
        return {
            "SSH_MULTIPLICATION_PORT": self.SSH_MULTIPLICATION_PORT,
            "UDP_MULTIPLICATION_PORT": self.UDP_MULTIPLICATION_PORT,
            "BASE_GATEWAY_PORT": self.BASE_GATEWAY_PORT,
        }

    def get_gateway_ip(self):
        return {"gateway_ip": self.GATEWAY_IP}

    def create_mount_init_script(self, new_volumes=None, attach_volumes=None):
        logger.info(f"Create init script for volume ids:{new_volumes}")
        if not new_volumes and not attach_volumes:
            return None

        fileDir = os.path.dirname(os.path.abspath(__file__))
        mount_script = os.path.join(fileDir, "scripts/bash/mount.sh")

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
        name,
        udp_port_start=None,
        ssh=True,
        udp=False,
        description=None,
        research_environment_metadata=None,
    ):
        logger.info(f"Create new security group {name}")
        sec = self.openstack_connection.get_security_group(name_or_id=name)
        if sec:
            logger.info("Security group with name {} already exists.".format(name))
            return sec
        new_security_group = self.openstack_connection.create_security_group(
            name=name, description=description
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
            logger.info("Add ssh rule to security group {}".format(name))

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
        self, research_environment_metadata, servername
    ):
        custom_security_groups = []

        custom_security_groups.append(
            self.create_security_group(
                name=servername + "_ssh", description="Only SSH"
            ).name
        )

        if research_environment_metadata:
            custom_security_groups.append(
                self.create_security_group(
                    name=servername + research_environment_metadata.security_group_name,
                    research_environment_metadata=research_environment_metadata,
                    description=research_environment_metadata.security_group_description,
                    ssh=research_environment_metadata.security_group_ssh,
                ).name
            )

        return custom_security_groups

    def get_limits(self):

        logger.info("Get Limits")
        limits = self.openstack_connection.get_compute_limits()
        limits.update(self.openstack_connection.get_volume_limits())
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

    def exist_server(self, name):

        if self.openstack_connection.compute.find_server(name) is not None:
            return True
        else:
            return False

    def get_server(self, openstack_id):
        logger.info(f"Get Server by id: {openstack_id}")
        try:
            server = self.openstack_connection.compute.get_server(openstack_id)
            return server
        except Exception as e:
            logger.exception("No Server found {0} | Error {1}".format(openstack_id, e))
            return None

    def resume_server(self, openstack_id):

        logger.info(f"Resume Server {openstack_id}")
        try:
            server = self.openstack_connection.get_server(openstack_id)
            if server is None:
                logger.exception(f"Instance {openstack_id} not found")
                raise NotFoundException(message=f"Instance {openstack_id} not found")
            self.openstack_connection.compute.start_server(server)
            return True

        except ConflictException as e:
            logger.exception(f"Resume Server {openstack_id} failed!")
            raise e

    def reboot_server(self, openstack_id, reboot_type):
        logger.info(f"Reboot Server {openstack_id} - {reboot_type}")
        server = self.openstack_connection.get_server(name_or_id=openstack_id)
        try:
            logger.info(f"Stop Server {openstack_id}")

            if server is None:
                logger.exception(f"Instance {openstack_id} not found")
                raise NotFoundException(message=f"Instance {openstack_id} not found")
            else:
                self.openstack_connection.compute.reboot_server(server, reboot_type)
                return True
        except ConflictException as e:
            logger.exception(f"Reboot Server {openstack_id} failed!")

            raise e

    def stop_server(self, openstack_id):

        logger.info(f"Stop Server {openstack_id}")
        server = self.openstack_connection.get_server(name_or_id=openstack_id)
        try:
            if server is None:
                logger.exception(f"Instance {openstack_id} not found")
                raise NotFoundException(message=f"Instance {openstack_id} not found")

            self.openstack_connection.compute.stop_server(server)
            return openstack_id

        except ConflictException as e:
            logger.exception(f"Stop Server {openstack_id} failed!")
            raise e

    def delete_server(self, openstack_id):

        logger.info(f"Delete Server {openstack_id}")
        try:
            server = self.openstack_connection.get_server(name_or_id=openstack_id)

            if not server:
                logger.error("Instance {0} not found".format(openstack_id))
                return False
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
            return True
        except ConflictException:
            logger.error(f"Delete Server {openstack_id} failed!")

            return False
        except Exception:
            logger.error(f"Delete Server {openstack_id} failed!")
            return False

    def get_vm_ports(self, openstack_id):
        logger.info(f"Get IP and PORT for server {openstack_id}")
        server = self.openstack_connection.get_server(name_or_id=openstack_id)
        server_base = int(server["private_v4"].split(".")[-1])
        ssh_port = (
            self.BASE_GATEWAY_PORT + int(server_base) * self.SSH_MULTIPLICATION_PORT
        )
        udp_port = (
            self.BASE_GATEWAY_PORT + int(server_base) * self.UDP_MULTIPLICATION_PORT
        )
        return {"port": str(ssh_port), "udp": str(udp_port)}

    def create_userdata(
        self, volume_ids_path_new, volume_ids_path_attach, additional_keys
    ):

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
        flavor,
        image,
        servername,
        metadata,
        public_key,
        research_environment_metadata,
        volume_ids_path_new=None,
        volume_ids_path_attach=None,
        additional_keys=None,
    ):
        logger.info(f"Start Server {servername}")
        custom_security_groups = self.prepare_security_groups_new_server(
            research_environment_metadata=research_environment_metadata,
            servername=servername,
        )
        key_name = None
        try:

            image = self.get_image(name_or_id=image)
            flavor = self.get_flavor(name_or_id=flavor)
            network = self.get_network()

            key_name = f"{metadata.get('elixir_id')[:-18]}{str(uuid4())[0:5]}"
            logger.info(f"Key name {key_name}")
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
            for id in volume_ids:
                volumes.append(self.openstack_connection.get_volume(name_or_id=id))
            init_script = self.create_userdata(
                volume_ids_path_new=volume_ids_path_new,
                volume_ids_path_attach=volume_ids_path_attach,
                additional_keys=additional_keys,
            )
            server = self.openstack_connection.create_server(
                name=servername,
                image=image["id"],
                flavor=flavor["id"],
                network=[network["id"]],
                key_name=key_name,
                meta=metadata,
                volumes=volumes,
                userdata=init_script,
                availability_zone=self.AVAILABILITY_ZONE,
                security_groups=self.DEFAULT_SECURITY_GROUPS + custom_security_groups,
            )

            openstack_id = server["id"]
            self.delete_keypair(key_name=key_name)

            return openstack_id

        except Exception as e:
            if key_name:
                self.delete_keypair(key_name=key_name)

            for security_group in custom_security_groups:
                self.openstack_connection.delete_security_group(security_group)
            logger.exception("Start Server {1} error:{0}".format(e, servername))
            return None

    def start_server_with_playbook(
        self,
        flavor,
        image,
        servername,
        metadata,
        research_environment_metadata,
        volume_ids_path_new=None,
        volume_ids_path_attach=None,
        additional_keys=None,
    ):
        logger.info(f"Start Server {servername}")
        custom_security_groups = self.prepare_security_groups_new_server(
            research_environment_metadata=research_environment_metadata,
            servername=servername,
        )
        key_name = None
        try:

            image = self.get_image(name_or_id=image)
            flavor = self.get_flavor(name_or_id=flavor)
            network = self.get_network()

            key_creation = self.openstack_connection.create_keypair(name=servername)

            try:
                private_key = key_creation["private_key"]
            except Exception:
                private_key = key_creation.__dict__["private_key"]
            volume_ids = []
            volumes = []
            if volume_ids_path_new:
                volume_ids.extend([vol["openstack_id"] for vol in volume_ids_path_new])
            if volume_ids_path_attach:
                volume_ids.extend(
                    [vol["openstack_id"] for vol in volume_ids_path_attach]
                )
            logger.info(f"volume ids {volume_ids}")
            for id in volume_ids:
                volumes.append(self.openstack_connection.get_volume(name_or_id=id))
            init_script = self.create_userdata(
                volume_ids_path_new=volume_ids_path_new,
                volume_ids_path_attach=volume_ids_path_attach,
                additional_keys=additional_keys,
            )
            server = self.openstack_connection.create_server(
                name=servername,
                image=image["id"],
                flavor=flavor["id"],
                network=[network["id"]],
                key_name=servername,
                meta=metadata,
                volumes=volumes,
                userdata=init_script,
                availability_zone=self.AVAILABILITY_ZONE,
                security_groups=self.DEFAULT_SECURITY_GROUPS + custom_security_groups,
            )

            openstack_id = server["id"]

            return openstack_id, private_key

        except Exception as e:
            if key_name:
                self.delete_keypair(key_name=key_name)

            for security_group in custom_security_groups:
                self.openstack_connection.delete_security_group(security_group)
            logger.exception("Start Server {1} error:{0}".format(e, servername))
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
    ):
        logger.info(f"Add machine to {cluster_id}")
        image = self.get_image(name_or_id=image, replace_inactive=True)
        flavor = self.get_flavor(name_or_id=flavor)
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
        logger.info("Created cluster machine:{}".format(server["id"]))

        return server["id"]

    def check_server_status(self, openstack_id):

        logger.info(f"Check Status VM {openstack_id}")
        try:
            server = self.openstack_connection.get_server(name_or_id=openstack_id)
        except Exception:
            logger.exception(f"No Server with id  {openstack_id} ")
            return {"status": VmStates.NOT_FOUND, "id": openstack_id}

        if server is None:
            logger.exception(f"No Server with id  {openstack_id} ")
            return {"status": VmStates.NOT_FOUND, "id": openstack_id}
        try:
            if server["status"] == VmStates.ACTIVE:
                server_base = int(server["private_v4"].split(".")[-1])
                port = self.BASE_GATEWAY_PORT + (
                    server_base * self.SSH_MULTIPLICATION_PORT
                )

                if self.netcat(host=self.GATEWAY_IP, port=port):
                    return server
                else:
                    server["status"] = VmStates.PORT_CLOSED
                    return server
            else:
                return server
        except Exception:
            logger.error(f"Check Status VM {openstack_id} failed")
            server["status"] = VmStates.ERROR

            return server
