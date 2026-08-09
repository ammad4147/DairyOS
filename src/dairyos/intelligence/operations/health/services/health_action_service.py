from dairyos.intelligence.operations.orchestration.models.operational_action import (
    OperationalAction,
)



class HealthActionService:
    """
    Converts farm health recommendations
    into operational farm actions.
    """


    def create_actions(
        self,
        report,
    ):

        actions = []


        for recommendation in (
            report.recommended_actions
        ):

            priority = (
                "high"
                if report.risk_level == "HIGH"
                else "medium"
            )


            actions.append(

                OperationalAction(

                    action_type="farm_health_review",

                    description=recommendation,

                    priority=priority,

                    status="pending",

                    source_decision=(
                        report.primary_concern
                    ),
                )

            )


        return actions
