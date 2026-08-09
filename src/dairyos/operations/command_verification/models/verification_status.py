from enum import Enum


class VerificationStatus(Enum):
    """
    Command verification lifecycle.
    """

    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    REQUIRES_FOLLOWUP = "REQUIRES_FOLLOWUP"
