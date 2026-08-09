from dairyos.intelligence.memory.gateway.memory_gateway import (
    MemoryGateway,
)


class KnowledgeMemoryBridge:
    """
    Connects Knowledge Intelligence with Memory Intelligence.

    Responsibilities:

    - transfer knowledge records into memory
    - preserve intelligence continuity

    Future extensions:

    - automatic memory promotion
    - semantic linking
    """


    def __init__(
        self,
        gateway: MemoryGateway,
    ):

        self.gateway = gateway


    def store_knowledge_memory(
        self,
        memory_id: str,
        content: str,
    ):

        return self.gateway.create_memory(
            memory_id=memory_id,
            memory_type="knowledge",
            content=content,
            source="knowledge",
            confidence=1.0,
        )
