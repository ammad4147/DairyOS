from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MemorySignal:
    """
    Represents a signal stored from an operational event.
    """

    source: str
    message: str
    created_at: datetime = field(
        default_factory=datetime.now
    )

