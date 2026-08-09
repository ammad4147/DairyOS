from dataclasses import dataclass
from datetime import datetime, field


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

