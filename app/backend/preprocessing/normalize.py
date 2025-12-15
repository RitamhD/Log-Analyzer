from app.backend.schemas.event import RawWindowsEvent
from app.backend.preprocessing.clean_text import clean_message

def normalize_event(event: RawWindowsEvent) -> dict:
    return {
        "agent_id": event.agent_id,
        "hostname": event.hostname,
        "timestamp": event.timestamp,
        "event_id": event.event_id,
        "channel": event.channel,
        "source": event.source,
        "level": event.level,

        "raw_message": event.message or "",
        "clean_message": clean_message(event.message or "")
    }
