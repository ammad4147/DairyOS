from dairyos.intelligence.workflow.repository.workflow_repository import (
    WorkflowRepository,
)


class MemoryWorkflowRepository(
    WorkflowRepository,
):

    def __init__(self):

        self._workflows = []

    def save(
        self,
        workflow,
    ):

        self._workflows.append(
            workflow
        )

    def get_all(
        self,
    ):

        return list(
            self._workflows
        )
