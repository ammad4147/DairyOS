from dataclasses import dataclass
from datetime import datetime

from .event_type import OperationalEventType


@dataclass
class OperationalEvent:
    """
    Represents an operational system event.
    """

    event_type: OperationalEventType
    source: str
    description: str
    created_at: datetime
