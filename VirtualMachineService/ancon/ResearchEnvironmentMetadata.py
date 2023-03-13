class ResearchEnvironmentMetadata:
    def __init__(
        self,
        name,
        port,
        security_group_name,
        security_group_description,
        security_group_ssh,
        direction,
        protocol,
        information_for_display,
        needs_forc_support,
        json_string,
    ):
        self.name = name
        self.port = port
        self.security_group_name = security_group_name
        self.security_group_description = security_group_description
        self.security_group_ssh = security_group_ssh
        self.direction = direction
        self.protocol = protocol
        self.information_for_display = information_for_display
        self.json_string = json_string
        self.needs_forc_support = needs_forc_support
