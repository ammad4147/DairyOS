from dairyos.intelligence.execution.repository.queue_repository import (
    QueueRepository,
)


class MemoryQueueRepository(
    QueueRepository,
):

    def __init__(self):

        self._items = []


    def save(
        self,
        queue,
    ):

        self._items.append(
            queue,
        )


    def get_all(
        self,
    ):

        return self._items
