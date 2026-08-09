from dairyos.intelligence.learning_feedback.integration.execution_learning_bridge import (
    ExecutionLearningBridge,
)


class MockGateway:

    def process_feedback(
        self,
        *args,
    ):

        return "learning"



def test_execution_learning_bridge():

    bridge = ExecutionLearningBridge(
        MockGateway()
    )

    result = bridge.learn_from_execution(
        "decision",
        "workflow",
        "completed",
        True,
        "good",
    )

    assert result == "learning"
