import json
import os

import redis
import requests
import yaml
from requests import Timeout
from util.logger import setup_custom_logger
from util.state_enums import VmTaskStates

from .backend.backend import Backend
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
        logger.info("Connect to redis")
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

    def get_users_from_backend(self, backend_id):
        logger.info(f"Get users from backend {backend_id}")
        get_url = f"{self.FORC_URL}/users/{backend_id}"
        try:
            response = requests.get(
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
            logger.info(msg="Get users for backend timed out. {0}".format(e))
            return []

    def delete_user_from_backend(self, user_id, backend_id, owner):
        logger.info(f"Delete user {user_id} from backend {backend_id}")
        delete_url = f"{self.FORC_URL}/users/{backend_id}"
        user_info = {
            "owner": owner,
            "user": user_id,
        }
        try:
            response = requests.delete(
                delete_url,
                json=user_info,
                timeout=(30, 30),
                headers={"X-API-KEY": self.FORC_API_KEY},
                verify=True,
            )
            return response.json()
        except Timeout as e:
            logger.info(msg="Delete user from backend timed out. {0}".format(e))
            return {"Error": "Timeout."}
        except Exception as e:
            logger.exception(e)
            return {"Error": "An Exception occured."}

    def delete_backend(self, backend_id):
        logger.info(f"Delete Backend {backend_id}")
        delete_url = f"{self.FORC_URL}/backends/{backend_id}"
        try:
            response = requests.delete(
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
                return True
        except Timeout:
            logger.exception(msg="delete_backend timed out")
            return False

    def add_user_to_backend(self, user_id, backend_id, owner):
        logger.info(f"Add User {user_id} to backend {backend_id}")
        try:
            post_url = f"{self.FORC_URL}/users/{backend_id}"
            user_info = {
                "owner": owner,
                "user": user_id,
            }
        except Exception as e:
            logger.exception(e)
            return {"Error": "Could not create url or json body."}
        try:
            response = requests.post(
                post_url,
                json=user_info,
                timeout=(30, 30),
                headers={"X-API-KEY": self.FORC_API_KEY},
                verify=True,
            )
            try:
                data = response.json()
            except Exception as e:
                logger.exception(e)
                return {"Error": "Error in POST."}
            return data
        except Timeout as e:
            logger.info(msg="add user to backend timed out. {0}".format(e))
            return {"Error": "Timeout."}
        except Exception as e:
            logger.exception(e)
            return {"Error": "An error occured."}

    def create_backend(self, owner, user_key_url, template, upstream_url):
        logger.info(
            f"Create Backend - [Owner:{owner}, user_key_url:{user_key_url}, template:{template}, upstream_url:{upstream_url}"
        )
        template_version = self.template.get_template_version_for(template=template)
        if template_version is None:
            logger.warning(
                f"No suitable template version found for {template}. Aborting backend creation!"
            )
            return {}
        try:
            post_url = f"{self.FORC_URL}/backends/"
            backend_info = {
                "owner": owner,
                "user_key_url": user_key_url,
                "template": template,
                "template_version": template_version,
                "upstream_url": upstream_url,
            }
        except Exception as e:
            logger.exception(e)
            return {}
        try:
            response = requests.post(
                post_url,
                json=backend_info,
                timeout=(30, 30),
                headers={"X-API-KEY": self.FORC_API_KEY},
                verify=True,
            )
            try:
                data = response.json()
            except Exception as e:
                logger.exception(e)
                return {}
            logger.info(f"Backend created {data}")
            new_backend = Backend(
                id=data["id"],
                owner=data["owner"],
                location_url=data["location_url"],
                template=data["template"],
                template_version=data["template_version"],
            )
            return new_backend.to_dict()

        except Timeout as e:
            logger.info(msg="create_backend timed out. {0}".format(e))
            return {}
        except Exception as e:
            logger.exception(e)
            return {}

    def get_backends(self):
        logger.info("Get Backends")
        get_url = f"{self.FORC_URL}/backends/"
        try:
            response = requests.get(
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
            logger.exception(msg="create_backend timed out. {0}".format(e))
            return None

    def get_backends_by_template(self, template):
        logger.info(f"Get Backends by template: {template}")
        get_url = f"{self.FORC_URL}/backends/byTemplate/{template}"
        try:
            response = requests.get(
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
            logger.exception(msg="create_backend timed out. {0}".format(e))
            return None

    def get_backend_by_id(self, id):
        logger.info(f"Get backends by id: {id}")
        get_url = f"{self.FORC_URL}/backends/{id}"
        try:
            response = requests.get(
                get_url,
                timeout=(30, 30),
                headers={"X-API-KEY": self.FORC_API_KEY},
                verify=True,
            )
            try:
                data = response.json()
            except Exception as e:
                logger.exception(e)
                return {}
            return Backend(
                id=data["id"],
                owner=data["owner"],
                location_url=data["location_url"],
                template=data["template"],
                template_version=data["template_version"],
            )
        except Timeout as e:
            logger.exception(msg="create_backend timed out. {0}".format(e))
            return None

    def get_backends_by_owner(self, owner):
        logger.info(f"Get backends by owner: {owner}")
        get_url = f"{self.FORC_URL}/backends/byOwner/{owner}"
        try:
            response = requests.get(
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
            logger.exception(msg="create_backend timed out. {0}".format(e))
            return None

    def has_forc(self):
        logger.info("Check has forc")
        return self.FORC_URL is not None

    def get_forc_url(self):
        logger.info("Get Forc Url")
        return self.FORC_URL

    def load_env(self):
        logger.info("Load env: FORC")
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
        logger.info(f"Set vm {openstack_id}: {VmTaskStates.PREPARE_PLAYBOOK_BUILD} ")
        self.redis_connection.hmset(
            openstack_id,
            dict(
                key=private_key, name=name, status=VmTaskStates.PREPARE_PLAYBOOK_BUILD
            ),
        )

    def get_playbook_status(self, server):
        openstack_id = server.openstack_id
        logger.info(f"Get VM {openstack_id} Playbook status")

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
        logger.info(f"Get Metadata Research environment: {research_environment}")
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
        return 0
