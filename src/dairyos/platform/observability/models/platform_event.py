from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class PlatformEvent:
    event_type: str
    source: str
    payload: dict
    timestamp: datetime = datetime.now(UTC)
