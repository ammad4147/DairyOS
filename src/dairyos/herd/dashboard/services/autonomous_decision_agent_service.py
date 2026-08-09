from ..models.autonomous_decision_agent import AutonomousDecisionAgent



class AutonomousDecisionAgentService:



    def decide(

        self,

        condition

    ):


        if (

            "milk" in condition.lower()

            or

            "production" in condition.lower()

        ):

            return AutonomousDecisionAgent(

                condition,

                "Feed Investigation",

                87,

                "HIGH",

                [

                    "Review ration",

                    "Check health",

                    "Verify environment"

                ]

            )



        return AutonomousDecisionAgent(

            condition,

            "General Review",

            50,

            "MEDIUM",

            [

                "Review condition"

            ]

        )
