from dataclasses import dataclass
from datetime import datetime, timezone



@dataclass
class CommandAlert:

    title: str

    category: str

    severity: str

    entity_type: str

    entity_id: str

    status: str = "open"

    created_at: datetime = datetime.now(
        timezone.utc
    )

