from dairyos.intelligence.workflow.models.workflow_result import (
    WorkflowResult,
)


class WorkflowHistoryService:
    """
    Records workflow outcomes.
    """

    def record(
        self,
        workflow_type: str,
        success: bool,
        result: str,
        feedback: str,
    ) -> WorkflowResult:

        return WorkflowResult(
            workflow_type=workflow_type,
            success=success,
            result=result,
            feedback=feedback,
        )
