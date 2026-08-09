from dairyos.intelligence.execution.models.execution_status import (
    ExecutionStatus,
)


class ExecutionMonitor:
    """
    Tracks execution progress.
    """

    def update(
        self,
        workflow_type: str,
        current_status: str,
        previous_status: str,
    ) -> ExecutionStatus:

        return ExecutionStatus(
            workflow_type=workflow_type,
            current_status=current_status,
            previous_status=previous_status,
        )
