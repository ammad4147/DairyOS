from dairyos.intelligence.execution.services.execution_coordinator import (
    ExecutionCoordinator,
)


class WorkflowExecutionBridge:
    """
    Connects Workflow Intelligence with
    Execution Intelligence.
    """

    def __init__(self):

        self.coordinator = ExecutionCoordinator()


    def coordinator_instance(
        self,
    ):

        return self.coordinator
