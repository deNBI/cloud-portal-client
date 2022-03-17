import json
import os
from distutils.version import LooseVersion
from pathlib import Path

import requests
import yaml
from requests import Timeout
from ttypes import ResearchEnvironmentTemplate
from util.logger import setup_custom_logger

# from resenv.backend.Backend import Backend

TEMPLATE_NAME = "template_name"
BIOCONDA = "bioconda"
ALL_TEMPLATES = [BIOCONDA]
logger = setup_custom_logger(__name__)
FORC_VERSIONS = "forc_versions"
FORC_API_KEY = os.environ.get("FORC_API_KEY", None)
PORT = "port"
SECURITYGROUP_NAME = "securitygroup_name"
SECURITYGROUP_DESCRIPTION = "securitygroup_description"
SECURITYGROUP_SSH = "securitygroup_ssh"
DIRECTION = "direction"
PROTOCOL = "protocol"
INFORMATION_FOR_DISPLAY = "information_for_display"


class ResearchEnvironmentMetadata:
    def __init__(
        self,
        name: str,
        port: str,
        security_group_name: str,
        security_group_description: str,
        security_group_ssh: bool,
        direction: str,
        protocol: str,
        information_for_display: str,
    ):
        self.name = name
        self.port = port
        self.security_group_name = security_group_name
        self.security_group_description = security_group_description
        self.security_group_ssh = security_group_ssh
        self.direction = direction
        self.protocol = protocol
        self.information_for_display = information_for_display


class Template(object):
    def __init__(self, github_playbook_repo: str, forc_url: str, forc_api_key: str):
        self.GITHUB_PLAYBOOKS_REPO = github_playbook_repo
        self.FORC_URL = forc_url
        self.FORC_API_KEY = forc_api_key
        self._forc_allowed: dict[str, list[str]] = {}
        self._all_templates = [BIOCONDA]
        self._loaded_resenv_metadata: dict[str, ResearchEnvironmentMetadata] = {}
        self.update_playbooks()

    def get_loaded_resenv_metadata(self) -> dict[str, ResearchEnvironmentMetadata]:
        return self._loaded_resenv_metadata

    def update_playbooks(self) -> None:
        logger.info("STARTED update")
        r = requests.get(self.GITHUB_PLAYBOOKS_REPO)
        contents = json.loads(r.content)
        # Todo maybe clone entire direcotry
        for f in contents:
            if f["name"] != "LICENSE":
                logger.info("started download of " + f["name"])
                download_link = f["download_url"]
                file_request = requests.get(download_link)
                filename = Template.get_playbook_dir() + f["name"]
                with open(filename, "w") as playbook_file:
                    playbook_file.write(file_request.content.decode("utf-8"))
        templates_metadata: list[dict[str, str]] = Template.load_resenv_metadata()
        for template_metadata in templates_metadata:
            try:
                metadata = ResearchEnvironmentMetadata(
                    template_metadata[TEMPLATE_NAME],
                    template_metadata[PORT],
                    template_metadata[SECURITYGROUP_NAME],
                    template_metadata[SECURITYGROUP_DESCRIPTION],
                    bool(template_metadata[SECURITYGROUP_SSH]),
                    template_metadata[DIRECTION],
                    template_metadata[PROTOCOL],
                    template_metadata[INFORMATION_FOR_DISPLAY],
                )
                self.update_forc_allowed(template_metadata)
                if metadata.name not in list(self._loaded_resenv_metadata.keys()):
                    self._loaded_resenv_metadata[metadata.name] = metadata
                else:
                    if self._loaded_resenv_metadata[metadata.name] != metadata:
                        self._loaded_resenv_metadata[metadata.name] = metadata

            except Exception as e:
                logger.exception(
                    "Failed to parse Metadata yml: "
                    + str(template_metadata)
                    + "\n"
                    + str(e)
                )
        logger.info(f"Allowed Forc {self._forc_allowed}")

    def cross_check_forc_image(self, tags: list[str]) -> bool:
        get_url = f"{self.FORC_URL}/templates/"
        try:
            response = requests.get(
                get_url,
                timeout=(30, 30),
                headers={"X-API-KEY": FORC_API_KEY},
                verify=True,
            )
            if response.status_code != 200:
                return True
            else:
                templates = response.json()
        except Exception:
            logger.exception("Could not get templates from FORC.")
            templates = []
        cross_tags = list(set(self._all_templates).intersection(tags))
        for template_dict in templates:
            if (
                template_dict["name"] in self._forc_allowed
                and template_dict["name"] in cross_tags
            ):
                if (
                    template_dict["version"]
                    in self._forc_allowed[template_dict["name"]]
                ):
                    return True
        return False

    @staticmethod
    def get_playbook_dir() -> str:
        Path(f"{os.path.dirname(os.path.realpath(__file__))}/plays/").mkdir(
            parents=True, exist_ok=True
        )
        dir_path = f"{os.path.dirname(os.path.realpath(__file__))}/plays/"
        return dir_path

    @staticmethod
    def load_resenv_metadata() -> list[dict[str, str]]:
        templates_metada = []
        for file in os.listdir(Template.get_playbook_dir()):
            if "_metadata.yml" in file:
                with open(Template.get_playbook_dir() + file) as template_metadata:
                    try:
                        loaded_metadata = yaml.load(
                            template_metadata, Loader=yaml.FullLoader
                        )
                        template_name = loaded_metadata[TEMPLATE_NAME]

                        templates_metada.append(loaded_metadata)
                        if template_name not in ALL_TEMPLATES:
                            ALL_TEMPLATES.append(template_name)
                    except Exception:
                        logger.exception(f"Failed to parse Metadata yml: {file}")
        return templates_metada

    def get_template_version_for(self, template: str) -> str:
        template_versions: list[str] = self._forc_allowed.get(template)  # type: ignore
        if template_versions:
            return template_versions[0]
        return ""

    def get_allowed_templates(self) -> list[ResearchEnvironmentTemplate]:
        templates_metadata = []
        for file in os.listdir(Template.get_playbook_dir()):
            if "_metadata.yml" in file:
                with open(Template.get_playbook_dir() + file) as template_metadata:
                    try:
                        loaded_metadata = yaml.load(
                            template_metadata, Loader=yaml.FullLoader
                        )
                        template_name = loaded_metadata[TEMPLATE_NAME]
                        if loaded_metadata["needs_forc_support"]:
                            if template_name in list(self._forc_allowed.keys()):

                                research_environment_template = (
                                    ResearchEnvironmentTemplate(
                                        template_name=loaded_metadata["template_name"],
                                        title=loaded_metadata["title"],
                                        description=loaded_metadata["description"],
                                        logo_url=loaded_metadata["logo_url"],
                                        info_url=loaded_metadata["info_url"],
                                        port=int(loaded_metadata["port"]),
                                        incompatible_versions=loaded_metadata[
                                            "incompatible_versions"
                                        ],
                                        is_maintained=loaded_metadata["is_maintained"],
                                        information_for_display=loaded_metadata[
                                            "information_for_display"
                                        ],
                                    )
                                )
                                for (
                                    k,
                                    v,
                                ) in (
                                    research_environment_template.information_for_display.items()
                                ):
                                    research_environment_template.information_for_display[
                                        k
                                    ] = str(
                                        v
                                    )
                                templates_metadata.append(research_environment_template)
                                if template_name not in self._forc_allowed:
                                    ALL_TEMPLATES.append(template_name)
                            else:
                                logger.info(
                                    f"Failed to find supporting FORC file for {template_name}"
                                )
                        else:
                            research_environment_template = ResearchEnvironmentTemplate(
                                template_name=loaded_metadata["template_name"],
                                title=loaded_metadata["title"],
                                description=loaded_metadata["description"],
                                logo_url=loaded_metadata["logo_url"],
                                info_url=loaded_metadata["info_url"],
                                port=int(loaded_metadata["port"]),
                                incompatible_versions=loaded_metadata[
                                    "incompatible_versions"
                                ],
                                is_maintained=loaded_metadata["is_maintained"],
                                information_for_display=loaded_metadata[
                                    "information_for_display"
                                ],
                            )
                            for (
                                k,
                                v,
                            ) in (
                                research_environment_template.information_for_display.items()
                            ):
                                research_environment_template.information_for_display[
                                    k
                                ] = str(v)
                            templates_metadata.append(research_environment_template)
                            if template_name not in self._forc_allowed:
                                ALL_TEMPLATES.append(template_name)

                    except Exception as e:
                        logger.exception(
                            "Failed to parse Metadata yml: " + file + "\n" + str(e)
                        )
        return templates_metadata

    def update_forc_allowed(self, template_metadata: dict[str, str]) -> None:
        if template_metadata["needs_forc_support"]:
            name = template_metadata[TEMPLATE_NAME]
            allowed_versions = []
            for forc_version in template_metadata[FORC_VERSIONS]:
                get_url = f"{self.FORC_URL}/templates/{name}/{forc_version}"
                try:
                    response = requests.get(
                        get_url,
                        timeout=(30, 30),
                        headers={"X-API-KEY": self.FORC_API_KEY},
                        verify=True,
                    )
                    if response.status_code == 200:
                        allowed_versions.append(forc_version)
                except Timeout as e:
                    logger.info(f"checking template/version timed out. {e}")
            allowed_versions.sort(key=LooseVersion)
            allowed_versions.reverse()
            self._forc_allowed[name] = allowed_versions
