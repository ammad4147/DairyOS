from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LearningSignal:
    """
    Represents an intelligence learning observation.

    A learning signal captures patterns
    discovered from historical intelligence events.
    """


    category: str

    description: str

    confidence: float = 0.0

    source: str = (
        "intelligence_memory"
    )

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )
