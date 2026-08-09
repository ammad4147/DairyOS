from ..models.decision_optimization import DecisionOptimization



class DecisionOptimizationService:



    def optimize(

        self,

        condition,

        options

    ):


        best_action = max(

            options,

            key=options.get

        )


        confidence = options[best_action]



        return DecisionOptimization(

            condition,

            best_action,

            confidence,

            "Highest historical success probability"

        )
