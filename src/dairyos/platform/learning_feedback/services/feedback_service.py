from dairyos.platform.learning_feedback.models.feedback_signal import (
    FeedbackSignal,
)



class FeedbackService:
    """
    Captures operational learning feedback.
    """



    def __init__(self):

        self.signals = []



    def record(
        self,
        signal: FeedbackSignal,
    ):


        self.signals.append(signal)

        return signal



    def evaluate_effectiveness(
        self,
        recommendation_id,
    ):


        records = [

            item

            for item in self.signals

            if item.recommendation_id == recommendation_id

        ]


        if not records:

            return None



        return sum(

            item.effectiveness_score

            for item in records

        ) / len(records)

