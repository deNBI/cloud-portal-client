from util.logger import setup_custom_logger

logger = setup_custom_logger(__name__)


class Backend:
    def __init__(self, id, owner, location_url, template, template_version):

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
