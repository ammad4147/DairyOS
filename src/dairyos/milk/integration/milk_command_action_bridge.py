from dairyos.intelligence.command.services.command_execution_service import (
    CommandExecutionService,
)


class MilkCommandActionBridge:
    """
    Converts milk recommendations
    into executable command actions.
    """


    def create_action(
        self,
        recommendation,
        repository,
    ):

        service = CommandExecutionService(
            repository
        )


        action_type = (
            "MONITOR_MILK_STATUS"
        )


        if recommendation.urgency == "MEDIUM":

            action_type = (
                "INVESTIGATE_MILK_VARIANCE"
            )


        if recommendation.urgency == "HIGH":

            action_type = (
                "INVESTIGATE_MILK_DECLINE"
            )


        return service.execute(

            action_id=(
                "MILK-ACT-"
                +
                recommendation.recommendation_id
            ),

            recommendation_id=(
                recommendation.recommendation_id
            ),

            action_type=action_type,

            status="OPEN",

        )
