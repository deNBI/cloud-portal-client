import requests
import yaml
from ttypes import ClusterInfo, ClusterInstance
from util.logger import setup_custom_logger

logger = setup_custom_logger(__name__)


class BibigridConnector:
    def __init__(self, config_file: str):
        logger.info("Initializing Bibigrid Connector")

        self._BIBIGRID_URL: str = ""
        self._BIBIGRID_MODES: str = ""
        self._BIBIGRID_HOST: str = ""
        self._BIBIGRID_PORT: str = ""
        self._BIBIGRID_USE_MASTER_WITH_PUBLIC_IP: bool = False
        self._PRODUCTION_bool = True
        self.load_config_yml(config_file=config_file)

    def load_config_yml(self, config_file: str) -> None:

        with open(config_file, "r") as ymlfile:
            logger.info("Load config: Bibigrid")
            cfg = yaml.load(ymlfile, Loader=yaml.SafeLoader)
            self._NETWORK = cfg["openstack"]["network"]
            self._SUB_NETWORK = cfg["openstack"]["sub_network"]
            self._PRODUCTION = cfg["production"]
            self._AVAILABILITY_ZONE = cfg["openstack"]["availability_zone"]

            self._BIBIGRID_HOST = cfg["bibigrid"]["host"]
            self._BIBIGRID_PORT = cfg["bibigrid"]["port"]
            if cfg["bibigrid"].get("https", False):

                self._BIBIGRID_URL = (
                    f"https://{self._BIBIGRID_HOST}:{self._BIBIGRID_PORT}/bibigrid/"
                )
                self._BIBIGRID_EP = (
                    f"https://{self._BIBIGRID_HOST}:{self._BIBIGRID_PORT}"
                )
            else:
                self._BIBIGRID_URL = (
                    f"http://{self._BIBIGRID_HOST}:{self._BIBIGRID_PORT}/bibigrid/"
                )
                self.BIBIGRID_EP = f"http://{self._BIBIGRID_HOST}:{self._BIBIGRID_PORT}"
            self._BIBIGRID_MODES = cfg["bibigrid"]["modes"]
            self._BIBIGRID_USE_MASTER_WITH_PUBLIC_IP = cfg["bibigrid"].get(
                "use_master_with_public_ip", False
            )

    def get_cluster_status(self, cluster_id: str) -> dict[str, str]:
        logger.info(f"Get Cluster {cluster_id} status")
        headers = {"content-Type": "application/json"}
        body = {"mode": "openstack"}
        request_url = self._BIBIGRID_URL + "info/" + cluster_id
        response = requests.get(
            url=request_url,
            json=body,
            headers=headers,
            verify=self._PRODUCTION,
        )
        logger.info(f"Cluster {cluster_id} status: {str(response.content)} ")
        json_resp: dict[str, str] = response.json(strict=False)
        try:
            json_resp["log"] = str(json_resp["log"])
        except Exception:
            pass
        try:
            json_resp["msg"] = str(json_resp["msg"])
        except Exception:
            pass

        return json_resp

    def get_cluster_info(self, cluster_id: str) -> ClusterInfo:
        logger.info(f"Get Cluster info from {cluster_id}")
        infos: list[dict[str, str]] = self.get_clusters_info()
        for info in infos:
            if info["cluster-id"] == cluster_id:
                cluster_info = ClusterInfo(
                    launch_date=info["launch_date"],
                    group_id=info["group-id"],
                    network_id=info["network-id"],
                    public_ip=info["public-ip"],
                    subnet_id=info["subnet-id"],
                    user=info["user"],
                    inst_counter=info["# inst"],
                    cluster_id=info["cluster-id"],
                    key_name=info["key name"],
                )
                logger.info(f"Cluster {cluster_id} info: {cluster_info} ")

                return cluster_info

    def get_clusters_info(self) -> list[dict[str, str]]:
        logger.info("Get clusters info")
        headers = {"content-Type": "application/json"}
        body = {"mode": "openstack"}
        request_url = self._BIBIGRID_URL + "list"
        response = requests.get(
            url=request_url,
            json=body,
            headers=headers,
            verify=self._PRODUCTION,
        )
        infos: list[dict[str, str]] = response.json()["info"]
        return infos

    def is_bibigrid_available(self) -> bool:
        logger.info("Checking if Bibigrid is available")
        if not self._BIBIGRID_EP:
            logger.info("Bibigrid Url is not set")
            return False
        try:
            status = requests.get(self._BIBIGRID_EP + "/server/health").status_code
            if status == 200:
                logger.info("Bibigrid Server is available")
                return True

            else:

                logger.exception("Bibigrid is offline")
                return False

        except Exception:
            logger.exception("Bibigrid is offline")
            return False

    def terminate_cluster(self, cluster_id: str) -> dict[str, str]:
        logger.info(f"Terminate cluster: {cluster_id}")
        headers = {"content-Type": "application/json"}
        body = {"mode": "openstack"}
        response: dict[str, str] = requests.delete(
            url=f"{self._BIBIGRID_URL}terminate/{cluster_id}",
            json=body,
            headers=headers,
            verify=self._PRODUCTION,
        ).json()
        logger.info(response)
        return response

    def start_cluster(
        self,
        public_key: str,
        master_instance: ClusterInstance,
        worker_instances: list[ClusterInstance],
        user: str,
    ) -> dict[str, str]:
        logger.info(
            f"Start Cluster:\n\tmaster_instance: {master_instance}\n\tworker_instances:{worker_instances}\n\tuser:{user}"
        )
        master_instance = master_instance
        wI = []
        for wk in worker_instances:
            logger.info(wk)
            wI.append(wk)
        headers = {"content-Type": "application/json"}
        body = {
            "mode": "openstack",
            "subnet": self._SUB_NETWORK,
            "sshPublicKeys": [public_key],
            "user": user,
            "sshUser": "ubuntu",
            "availabilityZone": self._AVAILABILITY_ZONE,
            "masterInstance": master_instance,
            "workerInstances": wI,
            "useMasterWithPublicIp": self._BIBIGRID_USE_MASTER_WITH_PUBLIC_IP,
        }
        for mode in self._BIBIGRID_MODES:
            body.update({mode: True})
        request_url = self._BIBIGRID_URL + "create"
        response: dict[str, str] = requests.post(
            url=request_url,
            json=body,
            headers=headers,
            verify=self._PRODUCTION,
        ).json()
        logger.info(response)
        return response
