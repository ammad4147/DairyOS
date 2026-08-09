from dataclasses import dataclass
from datetime import datetime, timezone



@dataclass
class CommandAuditRecord:

    actor_id: str

    action: str

    entity_type: str

    entity_id: str

    result: str

    created_at: datetime = datetime.now(
        timezone.utc
    )

