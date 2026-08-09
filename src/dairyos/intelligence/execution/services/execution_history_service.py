from dairyos.intelligence.execution.models.execution_result import (
    ExecutionResult,
)


class ExecutionHistoryService:
    """
    Records execution outcomes.

    Future extensions:

    - audit history
    - KPI measurements
    - execution analytics
    """

    def record(
        self,
        workflow_type: str,
        success: bool,
        result: str,
        feedback: str,
    ) -> ExecutionResult:

        return ExecutionResult(
            workflow_type=workflow_type,
            success=success,
            result=result,
            feedback=feedback,
        )
