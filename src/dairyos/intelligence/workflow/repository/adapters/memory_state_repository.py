from dairyos.intelligence.workflow.repository.workflow_state_repository import (
    WorkflowStateRepository,
)


class MemoryStateRepository(
    WorkflowStateRepository,
):

    def __init__(self):

        self._states = []

    def save(
        self,
        state,
    ):

        self._states.append(
            state
        )

    def get_all(
        self,
    ):

        return list(
            self._states
        )
