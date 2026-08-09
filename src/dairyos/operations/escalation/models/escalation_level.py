from enum import Enum


class EscalationLevel(Enum):
    """
    Operational escalation hierarchy.
    """

    LEVEL_ONE = "LEVEL_ONE"
    LEVEL_TWO = "LEVEL_TWO"
    LEVEL_THREE = "LEVEL_THREE"
