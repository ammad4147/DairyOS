from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4



@dataclass
class OperationalEvent:
    """
    Immutable operational fact recorded by DairyOS.

    Represents something that happened
    in the real farm environment.
    """

    event_type: str

    entity_type: str

    entity_id: str

    actor: str

    payload: dict = field(
        default_factory=dict
    )

    event_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )
