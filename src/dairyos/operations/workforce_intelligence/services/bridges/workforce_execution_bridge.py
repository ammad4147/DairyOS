from dairyos.operations.workforce_intelligence.services.workforce_execution_service import (
    WorkforceExecutionService,
)


class WorkforceExecutionBridge:
    """
    Connects operational accountability
    with workforce execution intelligence.
    """


    def __init__(
        self,
        workforce_execution_service:
            WorkforceExecutionService,
    ):

        self.workforce_execution_service = (
            workforce_execution_service
        )



    def register_assignment_execution(
        self,
        assignment,
    ):

        return (
            self.workforce_execution_service
            .track_execution(
                user_id=assignment.user_id,
                action_id=assignment.action_id,
            )
        )



    def complete_assignment_execution(
        self,
        metric_id: str,
    ):

        return (
            self.workforce_execution_service
            .complete_execution(
                metric_id
            )
        )
