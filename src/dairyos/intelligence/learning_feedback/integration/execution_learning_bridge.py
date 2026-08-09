class ExecutionLearningBridge:
    """
    Connects execution intelligence
    with learning feedback intelligence.

    Flow:

    Execution
        |
        v
    Learning Feedback
    """


    def __init__(
        self,
        gateway,
    ):

        self.gateway = gateway


    def learn_from_execution(
        self,
        decision_type: str,
        workflow_type: str,
        execution_result: str,
        success: bool,
        feedback: str,
    ):

        return self.gateway.process_feedback(
            decision_type,
            workflow_type,
            execution_result,
            success,
            feedback,
        )
