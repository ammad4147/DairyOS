from ..models.daily_operating_board import DailyOperatingBoard


class DailyOperatingBoardService:


    def generate(

        self,

        command_center,

        actions

    ):


        critical_tasks = []


        for action in actions:

            critical_tasks.append(

                {

                    "priority": action.priority,

                    "category": action.category,

                    "action": action.action,

                    "urgency": action.urgency

                }

            )



        risk_count = 0

        if command_center.risk_level != "LOW":

            risk_count = 1



        pending_decisions = (

            1

            if command_center.decision_required

            else 0

        )



        status = (

            "ATTENTION REQUIRED"

            if risk_count > 0

            else "STABLE"

        )



        return DailyOperatingBoard(

            farm_name=command_center.farm_name,

            operating_status=status,

            critical_tasks=critical_tasks,

            risk_count=risk_count,

            pending_decisions=pending_decisions

        )
