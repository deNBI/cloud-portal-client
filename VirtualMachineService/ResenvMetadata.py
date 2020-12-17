class ResenvMetadata:
    def __init__(self, name, port_range_max, port_range_min, security_group_name, security_group_description, security_group_ssh, direction, protocol):
        self.name = name
        self.port_range_max = port_range_max
        self.port_range_min = port_range_min
        self.security_group_name = security_group_name
        self.security_group_description = security_group_description
        self.security_group_ssh = security_group_ssh
        self.direction = direction
        self.protocol = protocol