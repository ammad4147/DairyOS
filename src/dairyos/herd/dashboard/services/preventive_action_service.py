from ..models.preventive_action_plan import PreventiveActionPlan



class PreventiveActionService:



    def create_plan(

        self,

        category,

        risk_level

    ):


        priority = self._priority(

            risk_level

        )


        return PreventiveActionPlan(

            category,

            risk_level,

            priority,

            self._actions(category),

            self._timeline(risk_level),

            risk_level in (

                "HIGH",

                "CRITICAL"

            )

        )



    def _priority(

        self,

        risk_level

    ):


        priorities = {

            "CRITICAL": "URGENT",

            "HIGH": "HIGH",

            "MEDIUM": "NORMAL",

            "LOW": "LOW"

        }


        return priorities.get(

            risk_level,

            "NORMAL"

        )



    def _actions(

        self,

        category

    ):


        actions = {

            "PRODUCTION":

                [

                    "Review feed quality",

                    "Check production records",

                    "Review health indicators"

                ],


            "HEALTH":

                [

                    "Review animal health status",

                    "Check preventive measures",

                    "Schedule assessment"

                ],


            "REPRODUCTION":

                [

                    "Review breeding performance",

                    "Check conception indicators",

                    "Assess reproductive plan"

                ],


            "FINANCE":

                [

                    "Review financial trends",

                    "Assess cost drivers",

                    "Update planning"

                ]

        }


        return actions.get(

            category,

            [

                "Review farm indicators"

            ]

        )



    def _timeline(

        self,

        risk_level

    ):


        if risk_level in (

            "HIGH",

            "CRITICAL"

        ):

            return "Within 7 days"


        return "Monitor regularly"
