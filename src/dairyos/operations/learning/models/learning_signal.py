from dataclasses import dataclass
from datetime import datetime


@dataclass
class LearningSignal:
    """
    Captures an operational observation.
    """

    signal_id: str
    category: str
    description: str
    impact_level: str
    created_at: datetime
