"""
This Module implements an VirtualMachineHandler.

Which can be used for the PortalClient.
"""

from bibigrid_connector.bibigrid_connector import BibigridConnector
from forc_connector.forc_connector import ForcConnector
from openstack_connector.openstack_connector import OpenStackConnector
from util import thrift_converter
from util.logger import setup_custom_logger
from VirtualMachineService import Iface

logger = setup_custom_logger(__name__)


class VirtualMachineHandler(Iface):
    """Handler which the PortalClient uses."""

    def __init__(self, config_file):
        self.openstack_connector = OpenStackConnector(config_file=config_file)
        self.bibigrid_connector = BibigridConnector(config_file=config_file)
        self.forc_connector = ForcConnector(config_file=config_file)

    def get_images(self):
        return thrift_converter.os_to_thrift_images(
            openstack_images=self.openstack_connector.get_images()
        )

    def get_image(self, openstack_id):
        return thrift_converter.os_to_thrift_image(
            openstack_image=self.openstack_connector.get_image(name_or_id=openstack_id)
        )

    def get_public_images(self):
        return thrift_converter.os_to_thrift_images(
            openstack_images=self.openstack_connector.get_public_images()
        )

    def get_private_images(self):
        return thrift_converter.os_to_thrift_images(
            openstack_images=self.openstack_connector.get_private_images()
        )

    def get_flavors(self):
        return thrift_converter.os_to_thrift_flavors(
            openstack_flavors=self.openstack_connector.get_flavors()
        )

    def get_volume(self, volume_id):
        return thrift_converter.os_to_thrift_volume(
            openstack_volume=self.openstack_connector.get_volume(name_or_id=volume_id)
        )

    def get_volumes_by_ids(self, volume_ids):
        volumes = []
        for id in volume_ids:
            volumes.append(
                thrift_converter.os_to_thrift_volume(
                    openstack_volume=self.openstack_connector.get_volume(name_or_id=id)
                )
            )
        return volumes

    def resize_volume(self, volume_id, size):
        return self.openstack_connector.resize_volume(volume_id=volume_id, size=size)

    def get_gateway_ip(self):
        return self.openstack_connector.get_gateway_ip()

    def get_calculation_formulars(self):
        return self.openstack_connector.get_calculation_values()

    def import_keypair(self, keyname, public_key):
        return self.openstack_connector.import_keypair(
            keyname=keyname, public_key=public_key
        )

    def exist_server(self, name):
        return self.openstack_connector.exist_server(name=name)

    def get_vm_ports(self, openstack_id):
        return self.openstack_connector.get_vm_ports(openstack_id=openstack_id)

    def stop_server(self, openstack_id):
        return self.openstack_connector.stop_server(openstack_id=openstack_id)

    def delete_server(self, openstack_id):
        return self.openstack_connector.delete_server(openstack_id=openstack_id)

    def reboot_server(self, openstack_id, reboot_type):
        return self.openstack_connector.reboot_server(
            openstack_id=openstack_id, reboot_type=reboot_type
        )

    def resume_server(self, openstack_id):
        return self.openstack_connector.resume_server(openstack_id=openstack_id)

    def get_server(self, openstack_id):
        return thrift_converter.os_to_thrift_server(
            openstack_server=self.openstack_connector.get_server(
                openstack_id=openstack_id
            )
        )

    def get_servers(self):
        return thrift_converter.os_to_thrift_servers(
            openstack_servers=self.openstack_connector.get_servers()
        )

    def get_servers_by_ids(self, server_ids):
        return thrift_converter.os_to_thrift_servers(
            openstack_servers=self.openstack_connector.get_servers_by_ids(
                ids=server_ids
            )
        )

    def get_servers_by_bibigrid_id(self, bibigrid_id):
        return thrift_converter.os_to_thrift_servers(
            openstack_servers=self.openstack_connector.get_servers_by_bibigrid_id(
                bibigrid_id=bibigrid_id
            )
        )

    def get_playbook_logs(self, openstack_id):
        return self.forc_connector.get_playbook_logs(openstack_id=openstack_id)

    def has_forc(self):
        return self.forc_connector.has_forc()

    def get_forc_url(self):
        return self.forc_connector.get_forc_url()

    def create_snapshot(self, openstack_id, name, elixir_id, base_tags, description):
        return self.openstack_connector.create_snapshot(
            openstack_id=openstack_id,
            name=name,
            elixir_id=elixir_id,
            base_tags=base_tags,
            description=description,
        )

    def delete_image(self, image_id):
        return self.openstack_connector.delete_image(image_id=image_id)

    def create_volume(self, volume_name, volume_storage, metadata):
        return thrift_converter.os_to_thrift_volume(
            openstack_volume=self.openstack_connector.create_volume(
                volume_name=volume_name,
                volume_storage=volume_storage,
                metadata=metadata,
            )
        )

    def detach_volume(self, volume_id, server_id):
        return self.openstack_connector.detach_volume(
            volume_id=volume_id, server_id=server_id
        )

    def delete_volume(self, volume_id):
        return self.openstack_connector.delete_volume(volume_id=volume_id)

    def attach_volume_to_server(self, openstack_id, volume_id):
        return self.openstack_connector.attach_volume_to_server(
            openstack_id=openstack_id, volume_id=volume_id
        )

    def get_limits(self):
        return self.openstack_connector.get_limits()

    def create_backend(self, elixir_id, user_key_url, template, upstream_url):
        return self.forc_connector.create_backend(
            owner=elixir_id,
            user_key_url=user_key_url,
            template=template,
            upstream_url=upstream_url,
        )

    def delete_backend(self, id):
        return self.forc_connector.delete_backend(backend_id=id)

    def get_backends(self):
        return self.forc_connector.get_backends()

    def get_backends_by_owner(self, elixir_id):
        return self.forc_connector.get_backends_by_owner(owner=elixir_id)

    def get_backends_by_template(self, template):
        return self.forc_connector.get_backends_by_template(template=template)

    def get_backend_by_id(self, id):
        return self.forc_connector.get_backend_by_id(id=id)

    def add_user_to_backend(self, backend_id, owner_id, user_id):
        return self.forc_connector.add_user_to_backend(
            user_id=user_id, owner=owner_id, backend_id=backend_id
        )

    def get_users_from_backend(self, backend_id):
        return self.forc_connector.get_users_from_backend(backend_id=backend_id)

    def delete_user_from_backend(self, backend_id, owner_id, user_id):
        return self.forc_connector.delete_user_from_backend(
            user_id=user_id, backend_id=backend_id, owner=owner_id
        )

    def get_allowed_templates(self):
        return self.forc_connector.template.get_allowed_templates()

    def check_server_status(self, openstack_id):
        server = self.openstack_connector.check_server_status(openstack_id=openstack_id)
        # Check if playbook in progress
        server = self.forc_connector.get_playbook_status(server=server)

        return thrift_converter.os_to_thrift_server(openstack_server=server)

    def start_server(
        self,
        flavor,
        image,
        public_key,
        servername,
        metadata,
        research_environment,
        volume_ids_path_new,
        volume_ids_path_attach,
        additional_keys,
    ):
        if research_environment:
            research_environment_metadata = (
                self.forc_connector.get_metadata_by_research_environment(
                    research_environment=research_environment
                )
            )
        else:
            research_environment_metadata = None
        return self.openstack_connector.start_server(
            flavor=flavor,
            image=image,
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
        flavor,
        image,
        servername,
        metadata,
        research_environment,
        volume_ids_path_new,
        volume_ids_path_attach,
    ):
        if research_environment:
            research_environment_metadata = (
                self.forc_connector.get_metadata_by_research_environment(
                    research_environment=research_environment
                )
            )
        else:
            research_environment_metadata = None
        openstack_id, private_key = self.openstack_connector.start_server_with_playbook(
            flavor=flavor,
            image=image,
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
        self, public_key, playbooks_information, openstack_id
    ):
        port = self.openstack_connector.get_vm_ports(openstack_id=openstack_id)["port"]
        gateway_ip = self.openstack_connector.get_gateway_ip()["gateway_ip"]
        cloud_site = self.openstack_connector.CLOUD_SITE
        return self.forc_connector.create_and_deploy_playbook(
            public_key=public_key,
            playbooks_information=playbooks_information,
            openstack_id=openstack_id,
            port=port,
            ip=gateway_ip,
            cloud_site=cloud_site,
        )

    def bibigrid_available(self):
        return self.bibigrid_connector.bibigrid_available()

    def get_cluster_info(self, cluster_id):
        return self.bibigrid_connector.get_cluster_info(cluster_id=cluster_id)

    def get_cluster_status(self, cluster_id):
        return self.bibigrid_connector.get_cluster_status(cluster_id=cluster_id)

    def start_cluster(self, public_key, master_instance, worker_instances, user):
        return self.bibigrid_connector.start_cluster(
            public_key=public_key,
            master_instance=master_instance,
            worker_instances=worker_instances,
            user=user,
        )

    def terminate_cluster(self, cluster_id):
        return self.bibigrid_connector.terminate_cluster(cluster_id=cluster_id)

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
        return self.openstack_connector.add_cluster_machine(
            cluster_id=cluster_id,
            cluster_user=cluster_user,
            cluster_group_id=cluster_group_id,
            image=image,
            flavor=flavor,
            name=name,
            key_name=key_name,
            batch_idx=batch_idx,
            worker_idx=worker_idx,
        )
