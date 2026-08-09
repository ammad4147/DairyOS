from dataclasses import dataclass
from datetime import datetime


@dataclass
class OperationalAttention:
    """
    Represents an operational issue requiring management awareness.
    """

    attention_id: str
    title: str
    category: str
    priority: str
    description: str
    created_at: datetime

    resolved: bool = False

    def resolve(self) -> None:
        self.resolved = True
