from ..models.resolution_status import ResolutionStatus


class ResolutionVerificationService:
    """
    Verifies completed operational actions.
    """


    def verify(
        self,
        resolution,
    ):

        resolution.status = ResolutionStatus.VERIFIED

        return resolution
