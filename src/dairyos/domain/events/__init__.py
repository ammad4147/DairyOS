"""DairyOS domain event package."""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Event:
    """
    Base domain event.
    """

    name: str

    payload: Dict[str, Any]

    timestamp: str = ""


    def with_timestamp(
        self,
        timestamp: str,
    ):

        self.timestamp = timestamp

        self.payload["timestamp"] = timestamp

        return self


from dairyos.domain.events.operational_input_received import (
    OperationalInputReceived,
)


__all__ = [
    "Event",
    "OperationalInputReceived",
]
