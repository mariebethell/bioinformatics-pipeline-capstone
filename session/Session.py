from uuid import UUID
from ipaddress import IPv4Address, IPv6Address
from datetime import datetime

class Session:
    """
    Used by SessionManager to maintain user mappings
    
    """
    
    def __init__(self):
        self.pipeline_uuid: UUID
        self.user_ip: IPv4Address | IPv6Address
        self.last_update_time: datetime