from ..models.owner_action import OwnerAction


class OwnerActionService:


    def generate(

        self,

        command_center

    ):


        actions = []


        if command_center.decision_required:


            actions.append(

                OwnerAction(

                    priority=1,

                    category="EXECUTIVE DECISION",

                    action=command_center.recommended_action,

                    urgency=command_center.time_horizon,

                    business_impact=command_center.business_impact

                )

            )


        else:


            actions.append(

                OwnerAction(

                    priority=3,

                    category="OPERATIONS",

                    action="Maintain current operations",

                    urgency="Routine",

                    business_impact="No immediate risk"

                )

            )


        return sorted(

            actions,

            key=lambda x: x.priority

        )
