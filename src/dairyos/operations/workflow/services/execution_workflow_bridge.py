from dairyos.operations.execution.models.operational_execution import (
    OperationalExecution,
)


class ExecutionWorkflowBridge:
    """
    Connects operational execution
    with workflow lifecycle.
    """


    def execution_summary(
        self,
        execution: OperationalExecution,
    ) -> dict:
        """
        Creates workflow execution summary.
        """

        return {
            "execution_id": execution.execution_id,
            "action_id": execution.action_id,
            "assigned_to": execution.assigned_to,
            "status": execution.status,
            "completed": execution.is_completed(),
        }
