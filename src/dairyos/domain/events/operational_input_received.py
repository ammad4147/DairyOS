from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class OperationalInputReceived:
    """
    Domain event emitted whenever DairyOS
    receives a farm operational input.
    """

    input_type: str

    payload: dict[str, Any]

    source: str

    actor: str


    event_id: str = field(
        default_factory=lambda: str(uuid4())
    )


    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


    @property
    def name(
        self,
    ):
        """
        Canonical DairyOS event name.
        Required by PersistentEventJournal.
        """

        return "OperationalInputReceived"
