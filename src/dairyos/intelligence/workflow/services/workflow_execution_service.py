from dairyos.intelligence.workflow.models.workflow_execution import (
    WorkflowExecution,
)


class WorkflowExecutionService:
    """
    Executes enterprise workflows.
    """

    def start(
        self,
        workflow_type: str,
        executed_by: str,
        notes: str,
    ) -> WorkflowExecution:

        return WorkflowExecution(
            workflow_type=workflow_type,
            execution_status="running",
            executed_by=executed_by,
            notes=notes,
        )
