from uuid import UUID, uuid4
from datetime import datetime

class Session:
    """
    Used by SessionManager to maintain user mappings
    
    """
    
    def __init__(self, user_uuid: UUID, pipeline_uuid: UUID | None = None):
        self.session_id : UUID = uuid4()
        self.pipeline_uuid: UUID | None = pipeline_uuid
        self.user_uuid: UUID = user_uuid
        self.last_update_time: datetime = datetime.now()

    