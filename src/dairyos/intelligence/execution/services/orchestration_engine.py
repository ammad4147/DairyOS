from dairyos.intelligence.execution.services.execution_service import (
    ExecutionService,
)

from dairyos.intelligence.execution.services.task_dispatcher import (
    TaskDispatcher,
)

from dairyos.intelligence.execution.services.queue_manager import (
    QueueManager,
)


class OrchestrationEngine:
    """
    Enterprise execution orchestration engine.

    Converts workflow intent into
    executable operational units.
    """

    def __init__(self):

        self.execution_service = ExecutionService()

        self.task_dispatcher = TaskDispatcher()

        self.queue_manager = QueueManager()


    def orchestrate(
        self,
        workflow_type: str,
        objective: str,
        priority: str,
        task_name: str,
        assigned_to: str,
        queue_name: str,
    ):

        plan = self.execution_service.create(
            workflow_type=workflow_type,
            objective=objective,
            priority=priority,
        )


        task = self.task_dispatcher.dispatch(
            workflow_type=workflow_type,
            task_name=task_name,
            assigned_to=assigned_to,
        )


        queue = self.queue_manager.create(
            workflow_type=workflow_type,
            queue_name=queue_name,
            pending_tasks=1,
        )


        return {
            "plan": plan,
            "task": task,
            "queue": queue,
        }
