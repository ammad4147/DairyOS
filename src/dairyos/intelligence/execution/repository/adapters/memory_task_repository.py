from dairyos.intelligence.execution.repository.task_repository import (
    TaskRepository,
)


class MemoryTaskRepository(
    TaskRepository,
):

    def __init__(self):

        self._items = []


    def save(
        self,
        task,
    ):

        self._items.append(
            task,
        )


    def get_all(
        self,
    ):

        return self._items
