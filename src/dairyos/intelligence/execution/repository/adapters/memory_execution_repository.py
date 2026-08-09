from dairyos.intelligence.execution.repository.execution_repository import (
    ExecutionRepository,
)


class MemoryExecutionRepository(
    ExecutionRepository,
):

    def __init__(self):

        self._items = []


    def save(
        self,
        execution,
    ):

        self._items.append(
            execution,
        )


    def get_all(
        self,
    ):

        return self._items
