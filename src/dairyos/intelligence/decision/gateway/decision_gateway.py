"""
DairyOS Decision Gateway

Enterprise decision access boundary.
"""


class DecisionGateway:

    def __init__(self, service=None):

        if service is None:

            from dairyos.intelligence.decision.services.decision_service import (
                DecisionService,
            )

            from dairyos.intelligence.decision.repository.adapters.memory_decision_repository import (
                MemoryDecisionRepository,
            )

            repository = MemoryDecisionRepository()

            service = DecisionService(
                repository
            )

        self.service = service


    def evaluate(
        self,
        context=None,
    ):

        if hasattr(
            self.service,
            "evaluate",
        ):

            return self.service.evaluate(
                context
            )


        if hasattr(
            self.service,
            "decide",
        ):

            return self.service.decide(
                context
            )


        return []
