import json
import os

import requests
from requests import Timeout
from resenv.template.Template import Template
from VirtualMachineService.util.logger import setup_custom_logger

logger = setup_custom_logger(__name__)

TEMPLATE_NAME = "template_name"


class Backend:
    def __init__(self, id, owner, location_url, template, template_version):
        self.FORC_URL = "https://proxy-dev.bi.denbi.de:5000"
        self.FORC_API_KEY = os.environ.get("FORC_API_KEY", None)
        self.ID = id
        self.OWNER = owner
        self.LOCATION_URL = location_url
        self.TEMPLATE = template
        self.TEMPLATE_VERSION = template_version

    def to_dict(self):
        return {
            "id": self.ID,
            "owner": self.OWNER,
            "location_url": self.LOCATION_URL,
            "template": self.TEMPLATE,
            "template_version": self.TEMPLATE_VERSION,
        }

    def get_users_from_backend(self):
        get_url = f"{self.FORC_URL}/users/{self.ID}"
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

    def delete_user_from_backend(self, user_id):
        delete_url = f"{self.FORC_URL}/users/{self.ID}"
        user_info = {
            "owner": self.OWNER,
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

    def delete_backend(self):
        delete_url = f"{self.FORC_URL}/backends/{self.ID}"
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
            logger.exception(msg="create_backend timed out")
            return False

    #  @staticmethod
    # def has_forc():
    #    return RE_BACKEND_URL is not None

    # @staticmethod
    # def get_forc_url():
    #   if RE_BACKEND_URL is None:
    #      return ""
    # else:
    #    url = RE_BACKEND_URL.split(":5000", 1)[0]
    #   return f"{url}/"

    def add_user_to_backend(self, user_id):
        try:
            post_url = f"{self.FORC_URL}/users/{self.ID}"
            user_info = {
                "owner": self.OWNER,
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
            logger.info(msg="create_backend timed out. {0}".format(e))
            return {"Error": "Timeout."}
        except Exception as e:
            logger.exception(e)
            return {"Error": "An error occured."}

    def create_backend(self, upstream_url):
        template_version = Template.get_template_version_for(self.TEMPLATE)
        if template_version is None:
            logger.warning(
                f"No suitable template version found for {self.TEMPLATE}. Aborting backend creation!"
            )
            return {}
        try:
            post_url = f"{self.FORC_URL}/backends/"
            backend_info = {
                "owner": self.OWNER,
                "user_key_url": self.LOCATION_URL,
                "template": self.TEMPLATE,
                "template_version": self.TEMPLATE_VERSION,
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
