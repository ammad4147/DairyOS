from dairyos.intelligence.learning_feedback.services.feedback_coordinator import (
    FeedbackCoordinator,
)


class LearningGateway:
    """
    Gateway interface for learning feedback intelligence.

    Supports:
    - dependency injection for enterprise composition
    - default construction for standalone usage
    """


    def __init__(
        self,
        coordinator=None,
    ):

        if coordinator is None:
            coordinator = FeedbackCoordinator()

        self.coordinator = coordinator


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
            self.coordinator,
            "process_feedback",
        ):

            return self.coordinator.process_feedback(
                feedback
            )


        if hasattr(
            self.coordinator,
            "process",
        ):

            return self.coordinator.process(
                feedback
            )


        return feedback


    def analyze_learning(
        self,
        event,
    ):

        if hasattr(
            self.coordinator,
            "analyze_learning",
        ):

            return self.coordinator.analyze_learning(
                event
            )

        return None


    def get_status(
        self,
    ):

        return {
            "component": "learning_feedback_gateway",
            "status": "operational",
        }
