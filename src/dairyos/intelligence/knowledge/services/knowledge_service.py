from dairyos.intelligence.knowledge.models.knowledge_record import (
    KnowledgeRecord,
)


class KnowledgeService:
    """
    Enterprise knowledge management service.

    Responsibilities:

    - create knowledge records
    - validate knowledge metadata
    - expose stored knowledge

    Future extensions:

    - semantic indexing
    - knowledge graph integration
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository


    def create(
        self,
        knowledge_type: str,
        content: str,
        source: str,
        confidence: float,
    ) -> KnowledgeRecord:

        record = KnowledgeRecord(
            knowledge_type=knowledge_type,
            content=content,
            source=source,
            confidence=confidence,
        )

        self.repository.save(
            record
        )

        return record


    def get_all(
        self,
    ):

        return self.repository.get_all()
