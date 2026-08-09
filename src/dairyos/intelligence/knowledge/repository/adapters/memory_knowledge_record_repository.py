from dairyos.intelligence.knowledge.repository.knowledge_record_repository import (
    KnowledgeRecordRepository,
)


class MemoryKnowledgeRecordRepository(
    KnowledgeRecordRepository,
):

    def __init__(
        self,
    ):

        self._items = []


    def save(
        self,
        record,
    ):

        self._items.append(
            record
        )


    def get_all(
        self,
    ):

        return self._items
