class CommandOrchestrator:
    """
    Coordinates autonomous command flow.

    Responsibilities:

    - receive command requests
    - create operational recommendations
    - create executable command actions
    - return structured command result
    """


    def __init__(
        self,
        situation_service,
        recommendation_service,
        execution_service,
    ):

        self.situation_service = situation_service
        self.recommendation_service = recommendation_service
        self.execution_service = execution_service


    def execute(
        self,
        command=None,
    ):

        if command is None:
            return None


        recommendation = None


        if (
            self.recommendation_service
            and hasattr(
                self.recommendation_service,
                "create",
            )
        ):

            recommendation = (
                self.recommendation_service.create(
                    command.get(
                        "recommendation_id",
                        "rec-001",
                    ),
                    command.get(
                        "situation_id",
                        "situation-001",
                    ),
                    command.get(
                        "action",
                        "execute command",
                    ),
                    command.get(
                        "urgency",
                        "normal",
                    ),
                )
            )


        execution = None


        if (
            self.execution_service
            and hasattr(
                self.execution_service,
                "execute",
            )
        ):

            execution = (
                self.execution_service.execute(
                    command.get(
                        "action_id",
                        "action-001",
                    ),
                    recommendation.recommendation_id
                    if recommendation
                    else command.get(
                        "recommendation_id",
                        "rec-001",
                    ),
                    command.get(
                        "action_type",
                        "operational",
                    ),
                    command.get(
                        "status",
                        "created",
                    ),
                )
            )


        return {
            "recommendation": recommendation,
            "execution": execution,
        }
