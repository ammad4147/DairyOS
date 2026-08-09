from dairyos.platform.autonomy.learning.models.autonomy_feedback import (
    AutonomyFeedback,
)



class AutonomyLearningService:
    """
    Converts operational outcomes into learning signals.
    """



    def __init__(self):

        self.feedback = []



    def record(

        self,

        recommendation_id,

        outcome,

        confidence_change,

    ):


        signal = AutonomyFeedback(

            recommendation_id=recommendation_id,

            outcome=outcome,

            confidence_change=confidence_change,

        )


        self.feedback.append(signal)


        return signal



    def history(self):

        return self.feedback

