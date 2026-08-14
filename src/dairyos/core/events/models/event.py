from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from dairyos.core.time_utils import utcnow


@dataclass
class DairyEvent:

    event_type: str

    source: str

    data: dict[str, Any]

    created_at: datetime = field(
        default_factory=utcnow
    )
