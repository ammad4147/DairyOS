from dataclasses import dataclass
from datetime import datetime, timezone



@dataclass
class AuditRecord:

    actor_id: str

    actor_role: str

    action: str

    component: str

    entity_type: str

    entity_id: str

    details: dict

    created_at: datetime = datetime.now(
        timezone.utc
    )

