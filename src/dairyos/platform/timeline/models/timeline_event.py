from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class TimelineEvent:

    entity_type: str

    entity_id: str

    event_type: str

    description: str

    actor: str

    timestamp: datetime = datetime.now(
        UTC
    )

