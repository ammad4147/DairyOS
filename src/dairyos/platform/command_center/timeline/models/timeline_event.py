from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class TimelineEvent:

    event_type: str

    title: str

    entity_type: str

    entity_id: str

    actor: str

    severity: str

    created_at: datetime = datetime.now(
        UTC
    )

