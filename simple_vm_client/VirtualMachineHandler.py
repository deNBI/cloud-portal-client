"""
This Module implements an VirtualMachineHandler.

Which can be used for the PortalClient.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from bibigrid_connector.bibigrid_connector import BibigridConnector
from forc_connector.forc_connector import ForcConnector
from openstack_connector.openstack_connector import OpenStackConnector
from util import thrift_converter
from util.logger import setup_custom_logger
from VirtualMachineService import Iface

if TYPE_CHECKING:
    from ttypes import (
        VM,
        Backend,
        ClusterInfo,
        ClusterInstance,
        CondaPackage,
        Flavor,
        Image,
        PlaybookResult,
        ResearchEnvironmentTemplate,
        Volume,
    )

logger = setup_custom_logger(__name__)


class VirtualMachineHandler(Iface):
    """Handler which the PortalClient uses."""

    def __init__(self, config_file: str):
        self.openstack_connector = OpenStackConnector(config_file=config_file)
        self.bibigrid_connector = BibigridConnector(config_file=config_file)
        self.forc_connector = ForcConnector(config_file=config_file)

    def keyboard_interrupt_handler_playbooks(self) -> None:
        for k, v in self.forc_connector._active_playbooks.items():
            logger.info(f"Clearing traces of Playbook-VM for (openstack_id): {k}")
            self.openstack_connector.delete_keypair(
                key_name=self.forc_connector.redis_connection.hget(k, "name").decode(
                    "utf-8"
                )
            )
            v.stop(k)
            self.openstack_connector.delete_server(openstack_id=k)
        raise SystemExit(0)

    def get_images(self) -> list[Image]:
        images: list[Image] = thrift_converter.os_to_thrift_images(
            openstack_images=self.openstack_connector.get_images()
        )
        return images

    def get_image(self, openstack_id: str) -> Image:
        return thrift_converter.os_to_thrift_image(
            openstack_image=self.openstack_connector.get_image(name_or_id=openstack_id)
        )

    def get_public_images(self) -> list[Image]:
        return thrift_converter.os_to_thrift_images(
            openstack_images=self.openstack_connector.get_public_images()
        )

    def get_private_images(self) -> list[Image]:
        return thrift_converter.os_to_thrift_images(
            openstack_images=self.openstack_connector.get_private_images()
        )

    def get_flavors(self) -> list[Flavor]:
        return thrift_converter.os_to_thrift_flavors(
            openstack_flavors=self.openstack_connector.get_flavors()
        )

    def get_volume(self, volume_id: str) -> Volume:
        return thrift_converter.os_to_thrift_volume(
            openstack_volume=self.openstack_connector.get_volume(name_or_id=volume_id)
        )

    def get_volumes_by_ids(self, volume_ids: list[str]) -> list[Volume]:
        volumes = []
        for id in volume_ids:
            volumes.append(
                thrift_converter.os_to_thrift_volume(
                    openstack_volume=self.openstack_connector.get_volume(name_or_id=id)
                )
            )
        return volumes

    def resize_volume(self, volume_id: str, size: int) -> None:
        return self.openstack_connector.resize_volume(volume_id=volume_id, size=size)

    def get_gateway_ip(self) -> dict[str, str]:
        return self.openstack_connector.get_gateway_ip()

    def get_calculation_values(self) -> dict[str, int]:
        return self.openstack_connector.get_calculation_values()

    def import_keypair(self, keyname: str, public_key: str) -> dict[str, str]:
        return self.openstack_connector.import_keypair(
            keyname=keyname, public_key=public_key
        )

    def exist_server(self, name: str) -> bool:
        return self.openstack_connector.exist_server(name=name)

    def get_vm_ports(self, openstack_id: str) -> dict[str, str]:
        return self.openstack_connector.get_vm_ports(openstack_id=openstack_id)

    def stop_server(self, openstack_id: str) -> None:
        return self.openstack_connector.stop_server(openstack_id=openstack_id)

    def delete_server(self, openstack_id: str) -> None:
        return self.openstack_connector.delete_server(openstack_id=openstack_id)

    def reboot_hard_server(self, openstack_id: str) -> None:
        return self.openstack_connector.reboot_hard_server(openstack_id=openstack_id)

    def reboot_soft_server(self, openstack_id: str) -> None:
        return self.openstack_connector.reboot_soft_server(openstack_id=openstack_id)

    def resume_server(self, openstack_id: str) -> None:
        return self.openstack_connector.resume_server(openstack_id=openstack_id)

    def get_server(self, openstack_id: str) -> VM:
        server = self.openstack_connector.get_server(openstack_id=openstack_id)
        server = self.forc_connector.get_playbook_status(server=server)
        server = thrift_converter.os_to_thrift_server(openstack_server=server)
        return server

    def get_servers(self) -> list[VM]:
        serv = thrift_converter.os_to_thrift_servers(
            openstack_servers=self.openstack_connector.get_servers()
        )
        return serv

    def get_servers_by_ids(self, server_ids: list[str]) -> list[VM]:
        return thrift_converter.os_to_thrift_servers(
            openstack_servers=self.openstack_connector.get_servers_by_ids(
                ids=server_ids
            )
        )

    def get_servers_by_bibigrid_id(self, bibigrid_id: str) -> list[VM]:
        return thrift_converter.os_to_thrift_servers(
            openstack_servers=self.openstack_connector.get_servers_by_bibigrid_id(
                bibigrid_id=bibigrid_id
            )
        )

    def get_playbook_logs(self, openstack_id: str) -> PlaybookResult:
        return self.forc_connector.get_playbook_logs(openstack_id=openstack_id)

    def has_forc(self) -> bool:
        return self.forc_connector.has_forc()

    def get_forc_url(self) -> str:
        return self.forc_connector.get_forc_url()

    def create_snapshot(
        self,
        openstack_id: str,
        name: str,
        username: str,
        base_tags: list[str],
        description: str,
    ) -> str:
        return self.openstack_connector.create_snapshot(
            openstack_id=openstack_id,
            name=name,
            username=username,
            base_tags=base_tags,
            description=description,
        )

    def delete_image(self, image_id: str) -> None:
        return self.openstack_connector.delete_image(image_id=image_id)

    def create_volume(
        self, volume_name: str, volume_storage: int, metadata: dict[str, str]
    ) -> Volume:
        return thrift_converter.os_to_thrift_volume(
            openstack_volume=self.openstack_connector.create_volume(
                volume_name=volume_name,
                volume_storage=volume_storage,
                metadata=metadata,
            )
        )

    def detach_volume(self, volume_id: str, server_id: str) -> None:
        return self.openstack_connector.detach_volume(
            volume_id=volume_id, server_id=server_id
        )

    def delete_volume(self, volume_id: str) -> None:
        return self.openstack_connector.delete_volume(volume_id=volume_id)

    def attach_volume_to_server(
        self, openstack_id: str, volume_id: str
    ) -> dict[str, str]:
        return self.openstack_connector.attach_volume_to_server(
            openstack_id=openstack_id, volume_id=volume_id
        )

    def get_limits(self) -> dict[str, str]:
        return self.openstack_connector.get_limits()

    def create_backend(
        self, username: str, user_key_url: str, template: str, upstream_url: str
    ) -> Backend:
        return self.forc_connector.create_backend(
            owner=username,
            user_key_url=user_key_url,
            template=template,
            upstream_url=upstream_url,
        )

    def delete_backend(self, id: str) -> None:
        return self.forc_connector.delete_backend(backend_id=id)

    def get_backends(self) -> list[Backend]:
        return self.forc_connector.get_backends()

    def get_backends_by_owner(self, username: str) -> list[Backend]:
        return self.forc_connector.get_backends_by_owner(owner=username)

    def get_backends_by_template(self, template: str) -> list[Backend]:
        return self.forc_connector.get_backends_by_template(template=template)

    def get_backend_by_id(self, id: str) -> Backend:
        return self.forc_connector.get_backend_by_id(id=id)

    def add_user_to_backend(
        self, backend_id: str, owner_id: str, user_id: str
    ) -> dict[str, str]:
        return self.forc_connector.add_user_to_backend(
            user_id=user_id, owner=owner_id, backend_id=backend_id
        )

    def get_users_from_backend(self, backend_id: str) -> list[str]:
        return self.forc_connector.get_users_from_backend(backend_id=backend_id)

    def delete_user_from_backend(
        self, backend_id: str, owner_id: str, user_id: str
    ) -> dict[str, str]:
        return self.forc_connector.delete_user_from_backend(
            user_id=user_id, backend_id=backend_id, owner=owner_id
        )

    def get_allowed_templates(self) -> list[ResearchEnvironmentTemplate]:
        return self.forc_connector.template.get_allowed_templates()

    def start_server(
        self,
        flavor_name: str,
        image_name: str,
        public_key: str,
        servername: str,
        metadata: dict[str, str],
        research_environment: str,
        volume_ids_path_new: list[dict[str, str]],
        volume_ids_path_attach: list[dict[str, str]],
        additional_keys: list[str],
    ) -> str:
        if research_environment:
            research_environment_metadata = (
                self.forc_connector.get_metadata_by_research_environment(
                    research_environment=research_environment
                )
            )
        else:
            research_environment_metadata = None
        return self.openstack_connector.start_server(
            flavor_name=flavor_name,
            image_name=image_name,
            public_key=public_key,
            servername=servername,
            metadata=metadata,
            volume_ids_path_new=volume_ids_path_new,
            volume_ids_path_attach=volume_ids_path_attach,
            additional_keys=additional_keys,
            research_environment_metadata=research_environment_metadata,
        )

    def start_server_with_custom_key(
        self,
        flavor_name: str,
        image_name: str,
        servername: str,
        metadata: dict[str, str],
        research_environment: str,
        volume_ids_path_new: list[dict[str, str]],
        volume_ids_path_attach: list[dict[str, str]],
    ) -> str:
        if research_environment:
            research_environment_metadata = (
                self.forc_connector.get_metadata_by_research_environment(
                    research_environment=research_environment
                )
            )
        else:
            research_environment_metadata = None
        openstack_id, private_key = self.openstack_connector.start_server_with_playbook(
            flavor_name=flavor_name,
            image_name=image_name,
            servername=servername,
            metadata=metadata,
            research_environment_metadata=research_environment_metadata,
            volume_ids_path_new=volume_ids_path_new,
            volume_ids_path_attach=volume_ids_path_attach,
        )
        self.forc_connector.set_vm_wait_for_playbook(
            openstack_id=openstack_id, private_key=private_key, name=servername
        )
        return openstack_id

    def create_and_deploy_playbook(
        self,
        public_key: str,
        openstack_id: str,
        conda_packages: list[CondaPackage],
        research_environment_template: str,
        create_only_backend: bool,
    ) -> int:
        port = int(
            self.openstack_connector.get_vm_ports(openstack_id=openstack_id)["port"]
        )
        gateway_ip = self.openstack_connector.get_gateway_ip()["gateway_ip"]
        cloud_site = self.openstack_connector.CLOUD_SITE
        return self.forc_connector.create_and_deploy_playbook(
            public_key=public_key,
            research_environment_template=research_environment_template,
            create_only_backend=create_only_backend,
            conda_packages=conda_packages,
            openstack_id=openstack_id,
            port=port,
            ip=gateway_ip,
            cloud_site=cloud_site,
        )

    def is_bibigrid_available(self) -> bool:
        return self.bibigrid_connector.is_bibigrid_available()

    def get_cluster_info(self, cluster_id: str) -> ClusterInfo:
        return self.bibigrid_connector.get_cluster_info(cluster_id=cluster_id)

    def get_cluster_status(self, cluster_id: str) -> dict[str, str]:
        return self.bibigrid_connector.get_cluster_status(cluster_id=cluster_id)

    def start_cluster(
        self,
        public_key: str,
        master_instance: ClusterInstance,
        worker_instances: list[ClusterInstance],
        user: str,
    ) -> dict[str, str]:
        return self.bibigrid_connector.start_cluster(
            public_key=public_key,
            master_instance=master_instance,
            worker_instances=worker_instances,
            user=user,
        )

    def terminate_cluster(self, cluster_id: str) -> dict[str, str]:
        return self.bibigrid_connector.terminate_cluster(cluster_id=cluster_id)

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
        return self.openstack_connector.add_cluster_machine(
            cluster_id=cluster_id,
            cluster_user=cluster_user,
            cluster_group_id=cluster_group_id,
            image_name=image_name,
            flavor_name=flavor_name,
            name=name,
            key_name=key_name,
            batch_idx=batch_idx,
            worker_idx=worker_idx,
        )
