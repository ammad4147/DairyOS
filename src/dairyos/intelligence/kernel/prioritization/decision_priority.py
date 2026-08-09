from dataclasses import dataclass


@dataclass
class DecisionPriority:
    """
    Represents calculated priority for an intelligence decision.
    """

    level: str
    score: int
    reason: str
