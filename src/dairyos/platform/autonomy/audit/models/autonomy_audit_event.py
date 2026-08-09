from dataclasses import dataclass
from datetime import datetime, timezone



@dataclass
class AutonomyAuditEvent:

    event_type: str

    entity_type: str

    entity_id: str

    actor: str

    details: dict

    created_at: datetime = datetime.now(
        timezone.utc
    )

