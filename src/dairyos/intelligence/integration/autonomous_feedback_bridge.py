"""
DairyOS Autonomous Feedback Bridge

Connects autonomous intelligence execution
outcomes with learning feedback processing.

Keeps runtime orchestration independent
from learning feedback implementation.
"""


class AutonomousFeedbackBridge:
    """
    Converts autonomous execution results
    into learning feedback events.
    """


    def __init__(
        self,
        learning_gateway=None,
    ):

        if learning_gateway is None:

            from dairyos.intelligence.learning_feedback.gateway.learning_gateway import (
                LearningGateway,
            )

            learning_gateway = LearningGateway()


        self.learning_gateway = learning_gateway



    def create_feedback(
        self,
        result: dict,
    ):

        decision = result.get(
            "decision"
        )


        execution = result.get(
            "execution"
        )


        success = (
            execution is not None
        )


        return {
            "decision": decision,
            "workflow": (
                "autonomous_intelligence"
            ),
            "result": execution,
            "success": success,
            "feedback": {
                "runtime_status": (
                    result.get(
                        "runtime",
                        {}
                    ).get(
                        "status"
                    )
                ),
                "stages": (
                    result.get(
                        "runtime",
                        {}
                    ).get(
                        "stages",
                        [],
                    )
                ),
            },
        }



    def process_cycle(
        self,
        result: dict,
    ):

        feedback = self.create_feedback(
            result
        )


        return self.learning_gateway.process_feedback(
            feedback
        )
