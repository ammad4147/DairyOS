from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class IntelligenceEvent:
    """
    Persistent intelligence event record.

    Represents a historical intelligence occurrence
    inside DairyOS.

    Used for:

    - audit history
    - decision traceability
    - operational learning
    - future event replay
    """


    event_type: str

    source: str

    payload: dict

    correlation_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    event_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )
