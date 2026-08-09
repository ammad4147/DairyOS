from enum import Enum


class OutcomeStatus(Enum):
    """
    Operational outcome status.
    """

    PENDING = "PENDING"
    SUCCESSFUL = "SUCCESSFUL"
    PARTIAL = "PARTIAL"
    UNSUCCESSFUL = "UNSUCCESSFUL"
