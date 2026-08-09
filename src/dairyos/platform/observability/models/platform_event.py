from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class PlatformEvent:
    event_type: str
    source: str
    payload: dict
    timestamp: datetime = datetime.now(timezone.utc)
