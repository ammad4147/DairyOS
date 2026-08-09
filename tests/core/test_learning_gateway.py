from dairyos.intelligence.learning_feedback.gateway.learning_gateway import (
    LearningGateway,
)


class MockCoordinator:

    def process(
        self,
        *args,
    ):

        return "processed"



def test_gateway_process():

    gateway = LearningGateway(
        MockCoordinator()
    )

    result = gateway.process_feedback(
        "decision",
        "workflow",
        "complete",
        True,
        "feedback",
    )

    assert result == "processed"
