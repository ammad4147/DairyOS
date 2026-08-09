from dairyos.intelligence.operations.orchestration.models.operational_action import (
    OperationalAction,
)


class FarmDecisionService:
    """
    Converts farm situations into operational actions.

    Responsibility:

    Farm condition -> Recommended operational response

    Does not execute actions.
    Does not assign staff.
    """


    def create_actions(
        self,
        situation,
    ):

        actions = []


        if situation.animals_requiring_attention > 0:

            actions.append(

                OperationalAction(

                    action_type="animal_review",

                    description=(
                        "Review animals requiring attention"
                    ),

                    priority="high",

                    status="pending",

                    source_decision=(
                        "Farm situation identified "
                        "animal attention requirement"
                    ),
                )

            )


        if situation.milk_change_percentage < -5:

            actions.append(

                OperationalAction(

                    action_type="production_investigation",

                    description=(
                        "Investigate milk production decline"
                    ),

                    priority="high",

                    status="pending",

                    source_decision=(
                        "Milk production declined "
                        "more than 5 percent"
                    ),
                )

            )


        if situation.reproduction_alerts > 0:

            actions.append(

                OperationalAction(

                    action_type="reproduction_review",

                    description=(
                        "Review reproduction alerts"
                    ),

                    priority="medium",

                    status="pending",

                    source_decision=(
                        "Reproduction alerts detected"
                    ),
                )

            )


        return actions
