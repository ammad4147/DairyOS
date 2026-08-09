from dairyos.intelligence.workflow.repository.workflow_result_repository import (
    WorkflowResultRepository,
)


class MemoryResultRepository(
    WorkflowResultRepository,
):

    def __init__(self):

        self._results = []

    def save(
        self,
        result,
    ):

        self._results.append(
            result
        )

    def get_all(
        self,
    ):

        return list(
            self._results
        )
