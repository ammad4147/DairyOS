from ..models.action_outcome import ActionOutcome



class ActionOutcomeService:



    def evaluate(

        self,

        action,

        completed,

        improvement

    ):


        if completed and improvement:

            status = "COMPLETED"

            outcome = "SUCCESS"

            learning = (

                f"{action} improved farm condition"

            )


        elif completed:

            status = "COMPLETED"

            outcome = "NO IMPROVEMENT"

            learning = (

                f"{action} requires review"

            )


        else:

            status = "PENDING"

            outcome = "UNKNOWN"

            learning = (

                "Action execution required"

            )



        return ActionOutcome(

            action,

            status,

            self._result(outcome),

            outcome,

            learning

        )



    def _result(

        self,

        outcome

    ):


        results = {

            "SUCCESS":

                "Condition improved",

            "NO IMPROVEMENT":

                "Further analysis required",

            "UNKNOWN":

                "Awaiting execution"

        }


        return results.get(

            outcome,

            "Review"

        )



    def successful(

        self,

        outcome

    ):


        return outcome.outcome == "SUCCESS"
