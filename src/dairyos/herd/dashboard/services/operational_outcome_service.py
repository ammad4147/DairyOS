from ..models.operational_outcome import OperationalOutcome



class OperationalOutcomeService:



    def evaluate(

        self,

        action,

        result

    ):


        success = (

            "improved" in result.lower()

            or "success" in result.lower()

        )


        if success:

            learning = (

                "Increase confidence for future interventions"

            )

        else:

            learning = (

                "Review intervention effectiveness"

            )


        return OperationalOutcome(

            action,

            result,

            success,

            learning

        )
