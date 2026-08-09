from dairyos.intelligence.execution.models.execution_task import (
    ExecutionTask,
)


class TaskDispatcher:
    """
    Dispatches execution tasks.
    """

    def dispatch(
        self,
        workflow_type: str,
        task_name: str,
        assigned_to: str,
    ) -> ExecutionTask:

        return ExecutionTask(
            workflow_type=workflow_type,
            task_name=task_name,
            assigned_to=assigned_to,
            status="assigned",
        )
