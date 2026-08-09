from dairyos.intelligence.command.models.command_action import (
    CommandAction,
)


class CommandExecutionService:
    """
    Creates command execution actions.
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository


    def execute(
        self,
        action_id: str,
        recommendation_id: str,
        action_type: str,
        status: str,
    ) -> CommandAction:

        action = CommandAction(
            action_id=action_id,
            recommendation_id=recommendation_id,
            action_type=action_type,
            status=status,
        )

        return self.repository.save(
            action
        )
