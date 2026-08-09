from dairyos.intelligence.execution.services.execution_service import (
    ExecutionService,
)

from dairyos.intelligence.execution.services.task_dispatcher import (
    TaskDispatcher,
)

from dairyos.intelligence.execution.services.queue_manager import (
    QueueManager,
)

from dairyos.intelligence.execution.services.execution_monitor import (
    ExecutionMonitor,
)

from dairyos.intelligence.execution.services.execution_history_service import (
    ExecutionHistoryService,
)

from dairyos.intelligence.execution.services.orchestration_engine import (
    OrchestrationEngine,
)


class ExecutionCoordinator:
    """
    Coordinates enterprise execution lifecycle.

    Maintains backward compatibility with
    autonomous intelligence runtime.
    """

    def __init__(self):

        self.execution_service = ExecutionService()

        self.task_dispatcher = TaskDispatcher()

        self.queue_manager = QueueManager()

        self.execution_monitor = ExecutionMonitor()

        self.history_service = ExecutionHistoryService()

        self.orchestration_engine = OrchestrationEngine()


    def execute(
        self,
        task=None,
        workflow_type=None,
        objective=None,
        priority=None,
        task_name=None,
        assigned_to=None,
        queue_name=None,
    ):

        #
        # Backward compatibility path
        #
        if task is not None and workflow_type is None:

            return task


        #
        # Enterprise orchestration path
        #
        return self.orchestration_engine.orchestrate(
            workflow_type=workflow_type,
            objective=objective,
            priority=priority,
            task_name=task_name,
            assigned_to=assigned_to,
            queue_name=queue_name,
        )
