from datetime import datetime

from ..models.command_verification import CommandVerification
from ..models.verification_status import VerificationStatus


class CommandVerificationService:
    """
    Creates command verification records.
    """


    def verify(
        self,
        verification_id,
        execution_id,
        success,
        message,
    ):

        if success:

            status = VerificationStatus.VERIFIED

        else:

            status = VerificationStatus.FAILED


        return CommandVerification(
            verification_id=verification_id,
            execution_id=execution_id,
            result_message=message,
            status=status,
            created_at=datetime.now(),
        )
