from dairyos.platform.command_center.learning.models.learning_feedback import (
    LearningFeedback,
)



class FeedbackService:
    """
    Converts operational outcomes into learning signals.
    """



    def __init__(self):

        self.feedback = []



    def record(
        self,
        signal: LearningFeedback,
    ):


        self.feedback.append(signal)


        return signal



    def all_feedback(self):

        return self.feedback

