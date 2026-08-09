from ..models.learning_signal import LearningSignal



class LearningFeedbackService:



    def evaluate(

        self,

        category,

        decision,

        outcome,

        success=True

    ):


        if success:

            effectiveness = "HIGH"

            adjustment = 15

            note = "Successful decision should improve future confidence"


        else:

            effectiveness = "LOW"

            adjustment = -10

            note = "Decision requires review before repeating"



        return LearningSignal(

            category,

            decision,

            outcome,

            effectiveness,

            adjustment,

            note

        )



    def confidence_score(

        self,

        signals

    ):


        if not signals:

            return 0


        return sum(

            signal.confidence_adjustment

            for signal in signals

        )



    def successful_actions(

        self,

        signals

    ):


        return [

            signal

            for signal in signals

            if signal.effectiveness == "HIGH"

        ]
