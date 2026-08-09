from enum import Enum


class ClosureStatus(Enum):
    """
    Operational closure states.
    """

    OPEN = "OPEN"
    REVIEW = "REVIEW"
    CLOSED = "CLOSED"
    ACCEPTED = "ACCEPTED"
