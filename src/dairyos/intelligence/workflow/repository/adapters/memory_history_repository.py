from dairyos.intelligence.workflow.repository.workflow_history_repository import (
    WorkflowHistoryRepository,
)


class MemoryHistoryRepository(
    WorkflowHistoryRepository,
):

    def __init__(self):

        self._history = []

    def save(
        self,
        history,
    ):

        self._history.append(
            history
        )

    def get_all(
        self,
    ):

        return list(
            self._history
        )
