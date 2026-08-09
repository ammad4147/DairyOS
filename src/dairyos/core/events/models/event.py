from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class DairyEvent:

    event_type: str

    source: str

    data: dict[str, Any]

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )
