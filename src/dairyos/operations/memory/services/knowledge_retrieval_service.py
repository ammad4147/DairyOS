
from ..models.operational_memory import OperationalMemory


class KnowledgeRetrievalService:
    """
    Retrieves operational knowledge.
    """

    def search(
        self,
        memories: list[OperationalMemory],
        category: str,
    ):

        return [
            memory
            for memory in memories
            if memory.pattern.category.lower()
            == category.lower()
        ]

