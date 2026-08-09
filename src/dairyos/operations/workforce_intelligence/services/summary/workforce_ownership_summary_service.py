from dairyos.operations.workforce_intelligence.services.workforce_ownership_service import (
    WorkforceOwnershipService,
)


class WorkforceOwnershipSummaryService:
    """
    Provides command center workforce ownership summary.
    """



    def __init__(
        self,
        ownership_service: WorkforceOwnershipService,
    ):

        self.ownership_service = (
            ownership_service
        )



    def generate_summary(
        self,
    ):

        snapshot = (
            self.ownership_service.generate_snapshot()
        )


        return snapshot
