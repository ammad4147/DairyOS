from enum import Enum


class ResolutionStatus(Enum):
    """
    Operational issue resolution states.
    """

    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    VERIFIED = "VERIFIED"
