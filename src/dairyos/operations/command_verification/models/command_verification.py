from dataclasses import dataclass
from datetime import datetime

from .verification_status import VerificationStatus


@dataclass
class CommandVerification:
    """
    Verification record for completed command.
    """

    verification_id: str
    execution_id: str
    result_message: str
    status: VerificationStatus
    created_at: datetime
