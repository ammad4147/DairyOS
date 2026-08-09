from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4



@dataclass
class OperationalCommand:
    """
    Represents an action requested
    by a farm user or system.
    """

    command_type: str

    actor: str

    payload: dict = field(
        default_factory=dict
    )

    command_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )
