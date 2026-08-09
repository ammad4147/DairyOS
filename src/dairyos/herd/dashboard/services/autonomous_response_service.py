from ..models.autonomous_response import AutonomousResponse



class AutonomousResponseService:



    def generate_response(

        self,

        condition

    ):


        if "milk" in condition.lower() or "production" in condition.lower():

            return AutonomousResponse(

                condition,

                "Feed Investigation",

                85,

                [

                    "Review ration",

                    "Check health",

                    "Verify environment"

                ]

            )


        return AutonomousResponse(

            condition,

            "General Review",

            50,

            [

                "Review condition"

            ]

        )
