from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .event_type import EventType
from .event_priority import EventPriority


@dataclass
class PlatformEvent:
    """
    Base enterprise event object.

    All DairyOS platform events inherit
    this communication contract.
    """

    name: str
    source: str

    event_type: EventType = EventType.SYSTEM_EVENT
    priority: EventPriority = EventPriority.NORMAL

    payload: dict[str, Any] = field(default_factory=dict)

    event_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    processed: bool = False

    def mark_processed(self) -> None:
        self.processed = True
