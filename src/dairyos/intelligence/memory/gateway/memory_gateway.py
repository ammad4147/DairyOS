class MemoryGateway:
    """
    Gateway for intelligence memory operations.
    """

    def __init__(self, service=None):

        if service is None:
            from dairyos.intelligence.memory.services.memory_service import (
                MemoryService,
            )

            from dairyos.intelligence.memory.repository.adapters.memory_memory_repository import (
                MemoryMemoryRepository,
            )

            service = MemoryService(
                MemoryMemoryRepository()
            )

        self.service = service


    def create_memory(self, *args, **kwargs):

        if kwargs:

            return self.service.create(
                kwargs.get("memory_id"),
                kwargs.get("memory_type"),
                kwargs.get("content"),
                kwargs.get("source"),
                kwargs.get("confidence"),
            )


        if len(args) == 1:

            memory = args[0]


            if isinstance(
                memory,
                dict,
            ):

                prediction = memory.get(
                    "prediction"
                )


                confidence = 0.0


                if prediction:

                    first_prediction = prediction[0]

                    if hasattr(
                        first_prediction,
                        "confidence",
                    ):

                        confidence = (
                            first_prediction.confidence
                        )


                return self.service.create(
                    "autonomous-memory-001",
                    "autonomous_intelligence",
                    str(memory),
                    "autonomous_decision_loop",
                    confidence,
                )


            return self.service.create(
                memory
            )


        return self.service.create(
            args[0],
            args[1],
            args[2],
            args[3],
            args[4],
        )


    def get_memories(self):

        if hasattr(
            self.service,
            "get_memories",
        ):
            return self.service.get_memories()

        if hasattr(
            self.service,
            "repository",
        ):

            repository = self.service.repository

            if hasattr(
                repository,
                "get_all",
            ):
                return repository.get_all()


        return []
