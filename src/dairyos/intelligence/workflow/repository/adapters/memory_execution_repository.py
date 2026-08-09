from dairyos.intelligence.workflow.repository.workflow_execution_repository import (
    WorkflowExecutionRepository,
)


class MemoryExecutionRepository(
    WorkflowExecutionRepository,
):

    def __init__(self):

        self._executions = []

    def save(
        self,
        execution,
    ):

        self._executions.append(
            execution
        )

    def get_all(
        self,
    ):

        return list(
            self._executions
        )
