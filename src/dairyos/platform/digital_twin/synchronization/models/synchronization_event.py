from dataclasses import dataclass
from datetime import datetime, timezone



@dataclass
class SynchronizationEvent:

    source: str

    event_type: str

    entity_id: str

    timestamp: datetime = datetime.now(
        timezone.utc
    )

