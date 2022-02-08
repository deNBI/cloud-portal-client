from celery import shared_task
from celery.app.log import TaskFormatter
from celery.signals import after_setup_task_logger, worker_process_init
from celery_config.debugtask import DebugTask
from logger import setup_custom_logger
from openstack_connector.openstack_connector import OpenStackConnector

logger = setup_custom_logger(__name__)


@after_setup_task_logger.connect
def setup_task_logger(logger, *args, **kwargs):
    for handler in logger.handlers:
        handler.setFormatter(
            TaskFormatter(
                "%(asctime)s - %(task_id)s - %(task_name)s - %(name)s - %(levelname)s - %(message)s"
            )
        )


@worker_process_init.connect
def init_worker(**kwargs):
    global openstack_connector

    logger.info("Initializing openstack connection for worker!")
    openstack_connector = OpenStackConnector()


def get_openstack_connector():
    global openstack_connector

    if not openstack_connector:
        openstack_connector = OpenStackConnector()
    return openstack_connector


@shared_task(base=DebugTask)
def get_flavor(name_or_id):
    return get_openstack_connector().get_flavor(name_or_id=name_or_id)


@shared_task(base=DebugTask)
def get_flavors():
    return get_openstack_connector().get_flavors()


@shared_task(base=DebugTask)
def create_snapshot(openstack_id, name, elixir_id, base_tags, description):
    return openstack_connector.create_snapshot(
        openstack_id=openstack_id,
        name=name,
        elixir_id=elixir_id,
        base_tags=base_tags,
        description=description,
    )


@shared_task(base=DebugTask)
def get_images():
    return get_openstack_connector().get_images()


@shared_task(base=DebugTask)
def get_image(name_or_id):
    return get_openstack_connector().get_image(name_or_id=name_or_id)


@shared_task(base=DebugTask)
def delete_image(image_id):
    return get_openstack_connector().delete_image(image_id=image_id)


@shared_task(base=DebugTask)
def attach_volume_to_server(openstack_id, volume_id):
    return get_openstack_connector().attach_volume_to_server(
        openstack_id=openstack_id, volume_id=volume_id
    )


@shared_task(base=DebugTask)
def create_volume(volume_name, volume_storage, metadata):
    return get_openstack_connector().create_volume(
        volume_name=volume_name, volume_storage=volume_storage, metadata=metadata
    )


@shared_task(base=DebugTask)
def resize_volume(volume_id, size):
    return get_openstack_connector().resize_volume(volume_id=volume_id, size=size)


@shared_task(base=DebugTask)
def get_volume(name_or_id):
    return get_openstack_connector().get_volume(name_or_id=name_or_id)


@shared_task(base=DebugTask)
def detach_volume(volume_id, server_id):
    return get_openstack_connector().detach_volume(
        volume_id=volume_id, server_id=server_id
    )


@shared_task(base=DebugTask)
def delete_volume(volume_id):
    return get_openstack_connector().delete_volume(volume_id=volume_id)


@shared_task(base=DebugTask)
def get_gateway_ip():
    return get_openstack_connector().get_gateway_ip()


@shared_task(base=DebugTask)
def heartbeat():
    return {"status": "connected"}


@shared_task(base=DebugTask)
def get_limits():
    return get_openstack_connector().get_limits()


@shared_task(base=DebugTask)
def get_calculation_values():
    return get_openstack_connector().get_calculation_values()


@shared_task(base=DebugTask)
def exist_server(name):
    return get_openstack_connector().exist_server(name=name)


@shared_task(base=DebugTask)
def resume_server(openstack_id):
    return get_openstack_connector().resume_server(openstack_id=openstack_id)


@shared_task(base=DebugTask)
def reboot_server(openstack_id, reboot_type):
    return get_openstack_connector().reboot_server(
        openstack_id=openstack_id, reboot_type=reboot_type
    )


@shared_task(base=DebugTask)
def stop_server(openstack_id):
    return get_openstack_connector().stop_server(openstack_id=openstack_id)


@shared_task(base=DebugTask)
def start_server(
    flavor,
    image,
    servername,
    metadata,
    https,
    http,
    resenv,
    public_key,
    volume_ids_path_new,
    volume_ids_path_attach,
    additional_keys,
):
    return get_openstack_connector().start_server(
        flavor=flavor,
        image=image,
        servername=servername,
        metadata=metadata,
        https=https,
        http=http,
        resenv=resenv,
        public_key=public_key,
        volume_ids_path_new=volume_ids_path_new,
        volume_ids_path_attach=volume_ids_path_attach,
        additional_keys=additional_keys,
    )


@shared_task(base=DebugTask)
def start_server_with_playbook(
    flavor,
    image,
    servername,
    metadata,
    https,
    http,
    resenv,
    volume_ids_path_new,
    volume_ids_path_attach,
    additional_keys,
):
    return get_openstack_connector().start_server_with_playbook(
        flavor=flavor,
        image=image,
        servername=servername,
        metadata=metadata,
        https=https,
        http=http,
        resenv=resenv,
        volume_ids_path_new=volume_ids_path_new,
        volume_ids_path_attach=volume_ids_path_attach,
        additional_keys=additional_keys,
    )


@shared_task(base=DebugTask)
def create_and_deploy_playbook(public_key, playbooks_information, openstack_id):
    return get_openstack_connector().create_and_deploy_playbook(
        public_key=public_key,
        playbooks_information=playbooks_information,
        openstack_id=openstack_id,
    )


@shared_task(base=DebugTask)
def check_server_status(openstack_id):
    return get_openstack_connector().check_server_status(openstack_id=openstack_id)


@shared_task(base=DebugTask)
def delete_server(openstack_id):
    return get_openstack_connector().delete_server(openstack_id=openstack_id)


@shared_task(base=DebugTask)
def get_playbook_logs(openstack_id):
    return get_openstack_connector().get_playbook_logs(openstack_id=openstack_id)
