import os

import redis
import yaml
from util.logger import setup_custom_logger
from util.state_enums import VmTaskStates

from .playbook.playbook import Playbook
from .template.template import Template

logger = setup_custom_logger(__name__)
BIOCONDA = "bioconda"


class ForcConnector:
    def __init__(self, config_file):
        logger.info("Initializing Forc Connector")

        self.FORC_URL = None
        self.FORC_REMOTE_ID = None
        self.GITHUB_PLAYBOOKS_REPO = None
        self.REDIS_HOST = None
        self.REDIS_PORT = None
        self.redis_pool = None
        self.redis_connection = None
        self._active_playbooks = {}

        self.load_config(config_file=config_file)
        self.load_env()
        self.connect_to_redis()
        self.template = Template(
            github_playbook_repo=self.GITHUB_PLAYBOOKS_REPO,
            forc_url=self.FORC_URL,
            forc_api_key=self.FORC_API_KEY,
        )

    def load_config(self, config_file):
        logger.info("Load config file: FORC")
        with open(config_file, "r") as ymlfile:
            cfg = yaml.load(ymlfile, Loader=yaml.SafeLoader)
            self.FORC_URL = cfg["forc"]["forc_url"]
            self.FORC_REMOTE_ID = cfg["forc"]["forc_security_group_id"]
            self.GITHUB_PLAYBOOKS_REPO = cfg["forc"]["github_playbooks_repo"]
            self.REDIS_HOST = cfg["redis"]["host"]
            self.REDIS_PORT = cfg["redis"]["port"]

    def connect_to_redis(self):
        self.redis_pool = redis.ConnectionPool(
            host=self.REDIS_HOST, port=self.REDIS_PORT
        )
        self.redis_connection = redis.Redis(
            connection_pool=self.redis_pool, charset="utf-8"
        )
        if self.redis_connection.ping():
            logger.info("Redis connection created!")
        else:
            logger.error("Could not connect to redis!")

    def load_env(self):
        self.FORC_API_KEY = os.environ.get("FORC_API_KEY", None)

    def get_playbook_logs(self, openstack_id):
        logger.info(f"Get Playbook logs {openstack_id}")
        if (
            self.redis_connection.exists(openstack_id) == 1
            and openstack_id in self._active_playbooks
        ):
            # key_name = self.redis_connection.hget(openstack_id, "name").decode("utf-8")
            playbook = self._active_playbooks.pop(openstack_id)
            status, stdout, stderr = playbook.get_logs()
            logger.info(f" Playbook logs{openstack_id} status: {status}")

            playbook.cleanup(openstack_id)
            # todo get outside
            # self.delete_keypair(key_name=key_name)
            return {"status": status, "stdout": stdout, "stderr": stderr}
        else:
            return {"status": 2, "stdout": "", "stderr": ""}

    def set_vm_wait_for_playbook(self, openstack_id, private_key, name):
        self.redis_connection.hmset(
            openstack_id,
            dict(
                key=private_key, name=name, status=VmTaskStates.PREPARE_PLAYBOOK_BUILD
            ),
        )

    def get_playbook_status(self, server):
        openstack_id = server.openstack_id

        if self.redis_connection.exists(openstack_id) == 1:
            if openstack_id in self._active_playbooks:
                logger.info(self._active_playbooks)
                playbook = self._active_playbooks[openstack_id]
                logger.info(playbook)

                playbook.check_status(openstack_id)
            status = self.redis_connection.hget(openstack_id, "status").decode("utf-8")
            if status == VmTaskStates.PREPARE_PLAYBOOK_BUILD:
                server.task_state = VmTaskStates.PREPARE_PLAYBOOK_BUILD
                return server
            elif status == VmTaskStates.BUILD_PLAYBOOK:
                server.task_state = VmTaskStates.BUILD_PLAYBOOK
                return server
            elif status == VmTaskStates.PLAYBOOK_FAILED:
                server.task_state = VmTaskStates.PLAYBOOK_FAILED
                return server
            else:
                return server
        return server

    def get_metadata_by_research_environment(self, research_environment):
        if research_environment in self.template.get_loaded_resenv_metadata():
            resenv_metadata = self.template.get_loaded_resenv_metadata()[
                research_environment
            ]
            return resenv_metadata
        elif (
            research_environment != "user_key_url" and research_environment != BIOCONDA
        ):
            logger.error(
                f"Failure to load metadata  of reasearch enviroment: {research_environment}"
            )
            return None

    def create_and_deploy_playbook(
        self, public_key, playbooks_information, openstack_id, port, ip, cloud_site
    ):

        logger.info(f"Starting Playbook for (openstack_id): {openstack_id}")
        key = self.redis_connection.hget(openstack_id, "key").decode("utf-8")
        playbook = Playbook(
            ip=ip,
            port=port,
            playbooks_information=playbooks_information,
            osi_private_key=key,
            public_key=public_key,
            pool=self.redis_pool,
            loaded_metadata_keys=list(
                self.template.get_loaded_resenv_metadata().keys()
            ),
            cloud_site=cloud_site,
        )
        self.redis_connection.hset(openstack_id, "status", VmTaskStates.BUILD_PLAYBOOK)
        playbook.run_it()
        self._active_playbooks[openstack_id] = playbook
        logger.info(f"Playbook for (openstack_id): {openstack_id} started!")
        return openstack_id
