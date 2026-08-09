"""
DairyOS Learning Feedback Coordination Service

Enterprise feedback orchestration boundary.
"""


class FeedbackCoordinator:

    def __init__(self, feedback_service=None):

        if feedback_service is None:

            from dairyos.intelligence.learning_feedback.services.learning_feedback_service import (
                LearningFeedbackService,
            )

            from dairyos.intelligence.learning_feedback.repository.adapters.memory_learning_feedback_repository import (
                MemoryLearningFeedbackRepository,
            )

            repository = MemoryLearningFeedbackRepository()

            feedback_service = LearningFeedbackService(
                repository
            )

        self.feedback_service = feedback_service


    def process_feedback(self, feedback):

        if hasattr(self.feedback_service, "process_feedback"):
            return self.feedback_service.process_feedback(feedback)

        return None


    def analyze_learning(self, event):

        if hasattr(self.feedback_service, "analyze_learning"):
            return self.feedback_service.analyze_learning(event)

        return None
