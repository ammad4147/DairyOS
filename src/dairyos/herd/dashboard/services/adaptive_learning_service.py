from ..models.adaptive_learning import AdaptiveLearning



class AdaptiveLearningService:



    def analyze(

        self,

        strategy,

        attempts,

        successes

    ):


        if attempts == 0:

            rate = 0

        else:

            rate = (successes / attempts) * 100



        if rate >= 80:

            adjustment = "INCREASE"

        elif rate >= 50:

            adjustment = "MAINTAIN"

        else:

            adjustment = "DECREASE"



        return AdaptiveLearning(

            strategy,

            attempts,

            successes,

            rate,

            adjustment

        )
