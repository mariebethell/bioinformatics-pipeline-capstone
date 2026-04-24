from uuid import UUID
from datetime import datetime

class Session:
    """
    Used by SessionManager to maintain user mappings
    
    """
    
    def __init__(self):
        self.pipeline_uuid: UUID
        self.user_uuid: UUID
        self.last_update_time: datetime