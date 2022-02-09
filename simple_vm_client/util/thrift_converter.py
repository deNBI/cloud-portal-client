import datetime
import time

from ttypes import VM, Flavor, Image, Volume
from util.logger import setup_custom_logger
from util.state_enums import VmStates

logger = setup_custom_logger(__name__)


def os_to_thrift_image(openstack_image):
    image_type = openstack_image.get("image_type", "image")

    image = Image(
        name=openstack_image["name"],
        min_disk=openstack_image["min_disk"],
        min_ram=openstack_image["min_ram"],
        status=openstack_image["status"],
        created_at=openstack_image["created_at"],
        updated_at=openstack_image["updated_at"],
        openstack_id=openstack_image["id"],
        description=openstack_image["metadata"].get("description", ""),
        tags=openstack_image.get("tags"),
        is_snapshot=image_type == "snapshot",
    )
    return image


def os_to_thrift_images(openstack_images):
    return [os_to_thrift_image(openstack_image=img) for img in openstack_images]


def os_to_thrift_flavor(openstack_flavor):
    flavor = Flavor(
        vcpus=openstack_flavor["vcpus"],
        ram=openstack_flavor["ram"],
        disk=openstack_flavor["disk"],
        name=openstack_flavor.get("name", None)
        or openstack_flavor.get("original_name", ""),
        tags=list(openstack_flavor["extra_specs"].keys()),
        ephemeral_disk=openstack_flavor["ephemeral"],
    )
    return flavor


def os_to_thrift_flavors(openstack_flavors):
    return [
        os_to_thrift_flavor(openstack_flavor=flavor) for flavor in openstack_flavors
    ]


def os_to_thrift_volume(openstack_volume):
    if not openstack_volume:
        return Volume(status=VmStates.NOT_FOUND)
    if openstack_volume.get("attachments"):
        device = openstack_volume.attachments[0].device
    else:
        device = None
    volume = Volume(
        status=openstack_volume.status,
        id=openstack_volume.ID,
        name=openstack_volume.name,
        description=openstack_volume.description,
        created_at=openstack_volume.created_at,
        device=device,
        size=openstack_volume.size,
    )
    return volume


def os_to_thrift_server(openstack_server):
    if not openstack_server:
        return VM(status=VmStates.NOT_FOUND)
    logger.debug(f"Convert server {openstack_server} to thrift server")
    fixed_ip = None
    floating_ip = None
    if openstack_server.get("OS-SRV-USG:launched_at", None):
        dt = datetime.datetime.strptime(
            openstack_server["OS-SRV-USG:launched_at"][:-7], "%Y-%m-%dT%H:%M:%S"
        )
        timestamp = time.mktime(dt.timetuple())
    else:
        timestamp = None
    flavor = os_to_thrift_flavor(openstack_server["flavor"])
    for values in openstack_server.addresses.values():
        for address in values:

            if address["OS-EXT-IPS:type"] == "floating":
                floating_ip = address["addr"]
            elif address["OS-EXT-IPS:type"] == "fixed":
                fixed_ip = address["addr"]

    server = VM(
        flavor=flavor,
        image=None,
        status=openstack_server["status"],
        metadata=openstack_server["metadata"],
        project_id=openstack_server["project_id"],
        keyname=openstack_server["key_name"],
        openstack_id=openstack_server["id"],
        name=openstack_server["name"],
        created_at=str(timestamp),
        task_state=openstack_server.get("task_state", None),
        vm_state=openstack_server.get("vm_state", None),
        power_state=openstack_server.get("power_state", None),
        fixed_ip=fixed_ip,
        floating_ip=floating_ip,
    )
    return server


def os_to_thrift_servers(openstack_servers):
    return [
        os_to_thrift_server(openstack_server=openstack_server)
        for openstack_server in openstack_servers
    ]
