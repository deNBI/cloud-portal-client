from enum import Enum

from .ttypes import Flavor, Image, VM, PlaybookResult, Backend, ClusterInfo, Volume
from ..logger import setup_custom_logger


logger = setup_custom_logger(__name__)


class VmTaskStates(Enum):
    SUSPENDING="SUSPENDING"
    PREPARE_PLAYBOOK_BUILD = "PREPARE_PLAYBOOK_BUILD"
    BUILD_PLAYBOOK = "BUILD_PLAYBOOK"
    PLAYBOOK_FAILED = "PLAYBOOK_FAILED"

class VmStates(Enum):
    BUILD = "BUILD"
    ACTIVE = "ACTIVE"
    ERROR = "ERROR"
    SHUTOFF = "SHUTOFF"
    NOT_FOUND = "NOT_FOUND"
    PORT_CLOSED = "PORT_CLOSED"


def convert_openstack_to_thrift_image(openstack_image):
    image = Image(
        name=openstack_image["name"],
        min_disk=openstack_image["min_disk"],
        min_ram=openstack_image["min_ram"],
        status=openstack_image["status"],
        created_at=openstack_image["created_at"],
        updated_at=openstack_image["updated_at"],
        openstack_id=openstack_image["id"],
        description=openstack_image["metadata"].get("description", ''),
        tags=openstack_image.get("tags"),
        is_snapshot=image_type == "snapshot",
    )
    return image


def convert_openstack_to_thrift_images(openstack_images):
    return [convert_openstack_to_thrift_image(openstack_image=img) for img in openstack_images]


def cv_os_to_thrift_flavor(openstack_flavor):
    flavor = Flavor(
        vcpus=openstack_flavor["vcpus"],
        ram=openstack_flavor["ram"],
        disk=openstack_flavor["disk"],
        name=openstack_flavor["name"],
        openstack_id=openstack_flavor["id"],
        tags=list(openstack_flavor["extra_specs"].keys()),
        ephemeral_disk=openstack_flavor["ephemeral"])
    return flavor


def cv_os_to_thrift_flavors(openstack_flavors):
    return [cv_os_to_thrift_flavor(openstack_flavor=flavor) for flavor in openstack_flavors]


def cv_os_to_thrift_volume(openstack_volume):
    if openstack_volume.get('attachments'):
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

