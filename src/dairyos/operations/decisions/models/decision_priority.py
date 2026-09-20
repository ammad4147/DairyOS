from dataclasses import dataclass


@dataclass
class DecisionPriority:
    """
    Priority classification for operational decisions.
    """

    level: str
    score: float

