from ..models.predictive_signal import PredictiveSignal



class PredictiveSignalService:



    def generate(

        self,

        category,

        observations,

        threshold=3

    ):


        if len(observations) >= threshold:

            risk = "HIGH"

            confidence = min(

                50 + (len(observations) * 10),

                95

            )

            pattern = (

                f"{len(observations)} consecutive "

                "changes detected"

            )


        else:

            risk = "NORMAL"

            confidence = 40

            pattern = "No significant pattern detected"



        return PredictiveSignal(

            category,

            pattern,

            risk,

            confidence,

            self._action(category)

        )



    def _action(

        self,

        category

    ):


        actions = {

            "PRODUCTION":

                "Review production factors",

            "HEALTH":

                "Review animal health indicators",

            "REPRODUCTION":

                "Review breeding indicators",

            "FINANCE":

                "Review financial trend"

        }


        return actions.get(

            category,

            "Continue monitoring"

        )



    def requires_prediction_action(

        self,

        signal

    ):


        return signal.risk == "HIGH"
