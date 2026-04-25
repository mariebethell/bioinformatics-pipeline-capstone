from uuid import UUID
from datetime import datetime

class Session:
    """
    Used by SessionManager to maintain user mappings
    
    """
    
    def __init__(self, user_uuid: UUID, pipeline_uuid: UUID | None = None):
        self.pipeline_uuid: UUID | None = pipeline_uuid
        self.user_uuid: UUID = user_uuid
        self.last_update_time: datetime = datetime.now()

    