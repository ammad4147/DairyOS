
from ..models.knowledge_pattern import KnowledgePattern
from ..models.operational_memory import OperationalMemory


class MemoryService:
    """
    Stores operational learning records.
    """

    def __init__(self):
        self.memories: list[OperationalMemory] = []


    def store(
        self,
        pattern: KnowledgePattern,
    ) -> OperationalMemory:

        memory = OperationalMemory(
            memory_id=f"MEM-{len(self.memories)+1:04d}",
            pattern=pattern,
        )

        self.memories.append(memory)

        return memory


    def get_all(self):

        return self.memories

