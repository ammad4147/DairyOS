from dataclasses import dataclass
from datetime import datetime


@dataclass
class DecisionPriority:
    """
    Priority classification for operational decisions.
    """

    level: str
    score: float

