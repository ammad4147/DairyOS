from dairyos.operations.workforce_intelligence.services.workforce_command_service import (
    WorkforceCommandService,
)



class WorkforceCommandSummaryService:
    """
    Provides consolidated workforce command summary.
    """



    def __init__(
        self,
        workforce_command_service: WorkforceCommandService,
    ):

        self.workforce_command_service = (
            workforce_command_service
        )



    def generate_summary(
        self,
    ):

        snapshot = (
            self.workforce_command_service.generate_snapshot()
        )


        return snapshot
