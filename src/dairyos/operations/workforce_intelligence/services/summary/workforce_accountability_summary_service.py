from dairyos.operations.workforce_intelligence.services.workforce_accountability_service import (
    WorkforceAccountabilityService,
)


class WorkforceAccountabilitySummaryService:
    """
    Provides command center workforce accountability summary.
    """


    def __init__(
        self,
        accountability_service: WorkforceAccountabilityService,
    ):

        self.accountability_service = (
            accountability_service
        )



    def generate_summary(
        self,
    ):

        snapshot = (
            self.accountability_service.generate_snapshot()
        )


        return snapshot
