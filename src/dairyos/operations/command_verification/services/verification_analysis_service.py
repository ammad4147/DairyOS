from ..models.verification_status import VerificationStatus


class VerificationAnalysisService:
    """
    Determines follow-up requirements.
    """


    def requires_followup(
        self,
        verification,
    ):

        return verification.status in [
            VerificationStatus.FAILED,
            VerificationStatus.REQUIRES_FOLLOWUP,
        ]
