"""
DairyOS Learning Gateway

Enterprise learning access boundary.
"""


class LearningGateway:

    def __init__(self, service=None):

        if service is None:

            from dairyos.intelligence.learning.services.learning_service import (
                LearningService,
            )

            from dairyos.intelligence.learning.repository.adapters.memory_learning_repository import (
                MemoryLearningRepository,
            )

            repository = MemoryLearningRepository()

            service = LearningService(
                repository
            )

        self.service = service


    def learn(
        self,
        signal=None,
    ):

        if hasattr(
            self.service,
            "learn",
        ):
            return self.service.learn(
                signal
            )

        return None


    def get_learning_signals(
        self,
    ):

        if hasattr(
            self.service,
            "get_learning_signals",
        ):
            return self.service.get_learning_signals()


        if hasattr(
            self.service,
            "repository",
        ):

            repository = self.service.repository

            if hasattr(
                repository,
                "list",
            ):
                return repository.list()


        return []


    def process_feedback(
        self,
        *args,
    ):

        if len(args) == 1:

            feedback = args[0]

        else:

            feedback = {
                "decision": args[0],
                "workflow": args[1],
                "result": args[2],
                "success": args[3],
                "feedback": args[4],
            }


        if hasattr(
            self.service,
            "process_feedback",
        ):
            return self.service.process_feedback(
                feedback
            )


        if hasattr(
            self.service,
            "learn",
        ):
            return self.service.learn(
                feedback
            )


        return feedback
