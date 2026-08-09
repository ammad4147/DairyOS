from dairyos.intelligence.knowledge.models.knowledge_record import (
    KnowledgeRecord,
)


class KnowledgeGateway:
    """
    Gateway for enterprise knowledge operations.
    """

    def __init__(self, service=None):

        if service is None:

            from dairyos.intelligence.knowledge.services.knowledge_service import (
                KnowledgeService,
            )

            from dairyos.intelligence.knowledge.repository.adapters.memory_knowledge_record_repository import (
                MemoryKnowledgeRecordRepository,
            )

            service = KnowledgeService(
                MemoryKnowledgeRecordRepository()
            )

        self.service = service


    def create(self, *args, **kwargs):

        if kwargs:

            return self.service.create(
                kwargs.get("knowledge_type"),
                kwargs.get("content"),
                kwargs.get("source"),
                kwargs.get("confidence"),
            )


        if len(args) == 1:

            return self.service.create(
                args[0]
            )


        return self.service.create(
            args[0],
            args[1],
            args[2],
            args[3],
        )


    def get_records(self):

        if hasattr(
            self.service,
            "get_records",
        ):
            return self.service.get_records()

        return []
