from ..models.decision_learning import DecisionLearning



class DecisionLearningService:



    def analyze(

        self,

        action,

        executions,

        successes

    ):


        if executions <= 0:

            confidence = 0

        else:

            confidence = int(

                (successes / executions) * 100

            )


        if confidence >= 75:

            strength = "HIGH"

        elif confidence >= 50:

            strength = "MEDIUM"

        else:

            strength = "LOW"



        return DecisionLearning(

            action,

            executions,

            successes,

            confidence,

            strength

        )



    def preferred_action(

        self,

        learning

    ):


        return learning.recommendation_strength == "HIGH"
