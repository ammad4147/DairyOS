from ..models.farm_command_center import FarmCommandCenter


class FarmCommandCenterService:


    def generate(

        self,

        executive_decision,

        daily_board

    ):


        status = "STABLE"


        if executive_decision.risk_level == "HIGH":

            status = "ATTENTION REQUIRED"


        elif executive_decision.risk_level == "MEDIUM":

            status = "MONITOR"



        priorities = []

        priorities.extend(

            executive_decision.recommendations

        )


        actions = []

        actions.extend(

            daily_board.owner_actions

        )



        return FarmCommandCenter(

            farm_name=daily_board.farm_name,

            operational_status=status,

            risk_level=executive_decision.risk_level,

            executive_score=getattr(

                executive_decision,

                "decision_score",

                0

            ),

            priorities=priorities,

            owner_actions=actions,

            active_alerts=len(actions)

        )
