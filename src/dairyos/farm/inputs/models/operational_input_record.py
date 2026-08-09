from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4
from typing import Any


@dataclass
class OperationalInputRecord:
    """
    Captured operational input received by DairyOS.

    Represents a farm activity input event
    before it is transformed into operational state.
    """

    input_type: str

    payload: dict[str, Any]

    source: str

    actor: str

    input_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    captured_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    validated: bool = False
