from dairyos.intelligence.execution.repository.history_repository import (
    HistoryRepository,
)


class MemoryHistoryRepository(
    HistoryRepository,
):

    def __init__(self):

        self._items = []


    def save(
        self,
        history,
    ):

        self._items.append(
            history,
        )


    def get_all(
        self,
    ):

        return self._items
