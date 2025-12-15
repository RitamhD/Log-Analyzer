from pydantic import BaseModel, Field
from typing import Optional, List


class RawWindowsEvent(BaseModel):
    event_id: int
    channel: str
    source: str = Field(..., alias="source_name")
    level: int = Field(..., alias="category")
    message: Optional[str]
    timestamp: str = Field(..., alias="time_generated")
    agent_id: str
    hostname: str

    class Config:
        extra = "allow"
        

class EventBatch(BaseModel):
    agent_id: str
    hostname: str
    batch_ts: str
    events: List[RawWindowsEvent]
