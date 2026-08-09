from dairyos.intelligence.execution.models.execution_queue import (
    ExecutionQueue,
)


class QueueManager:
    """
    Manages execution queues.
    """

    def create(
        self,
        workflow_type: str,
        queue_name: str,
        pending_tasks: int,
    ) -> ExecutionQueue:

        return ExecutionQueue(
            workflow_type=workflow_type,
            queue_name=queue_name,
            pending_tasks=pending_tasks,
            status="active",
        )
