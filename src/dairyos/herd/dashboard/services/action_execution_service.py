from ..models.farm_action import FarmAction



class ActionExecutionService:



    def create_action(

        self,

        recommendation,

        assigned_to="Farm Manager"

    ):


        return FarmAction(

            title=recommendation.recommendation,

            category=recommendation.category,

            priority=recommendation.priority,

            status="OPEN",

            assigned_to=assigned_to,

            timeframe=recommendation.timeframe

        )



    def complete_action(

        self,

        action

    ):


        action.status = "COMPLETED"

        action.completed = True


        return action



    def action_queue(

        self,

        recommendations

    ):


        return [

            self.create_action(item)

            for item in recommendations

        ]
