from dairyos.intelligence.execution.models.execution_plan import (
    ExecutionPlan,
)


class ExecutionService:
    """
    Creates execution plans from workflows.
    """

    def create(
        self,
        workflow_type: str,
        objective: str,
        priority: str,
    ) -> ExecutionPlan:

        return ExecutionPlan(
            workflow_type=workflow_type,
            objective=objective,
            priority=priority,
            status="planned",
        )
