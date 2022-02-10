from util.logger import setup_custom_logger

logger = setup_custom_logger(__name__)


class Backend:
    def __init__(
        self,
        id: str,
        owner: str,
        location_url: str,
        template: str,
        template_version: str,
    ):

        self.ID = id
        self.OWNER = owner
        self.LOCATION_URL = location_url
        self.TEMPLATE = template
        self.TEMPLATE_VERSION = template_version

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.ID,
            "owner": self.OWNER,
            "location_url": self.LOCATION_URL,
            "template": self.TEMPLATE,
            "template_version": self.TEMPLATE_VERSION,
        }
