from enum import Enum


class DecisionUrgency(Enum):
    """
    Management decision urgency.
    """

    NORMAL = "NORMAL"
    IMPORTANT = "IMPORTANT"
    URGENT = "URGENT"
    CRITICAL = "CRITICAL"
