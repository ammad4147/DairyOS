class LearningKnowledgeBridge:
    """
    Integration bridge between:

    Learning Feedback Intelligence
        ?
    Knowledge Intelligence
    """


    def __init__(
        self,
        knowledge_gateway,
    ):

        self.knowledge_gateway = knowledge_gateway


    def convert_learning(
        self,
        feedback,
    ):

        return self.knowledge_gateway.create(
            knowledge_type="learning_feedback",
            content=str(feedback),
            source="learning_engine",
            confidence=1.0,
        )
