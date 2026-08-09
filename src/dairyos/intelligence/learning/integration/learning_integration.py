from dairyos.intelligence.learning.gateway.learning_gateway import (
    LearningGateway,
)


class LearningIntegration:
    """
    Integration boundary between intelligence memory
    and learning intelligence.

    Converts historical intelligence records
    into learned operational knowledge.
    """


    def __init__(
        self,
        gateway: LearningGateway,
    ):

        self.gateway = gateway


    def process_history(
        self,
        events: list,
    ):

        return self.gateway.learn(
            events
        )


    def get_knowledge(
        self,
    ):

        return self.gateway.get_learning_signals()
