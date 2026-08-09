from dairyos.operations.command_center.models.operational_action import (
    OperationalAction,
)



class OperationalActionService:
    """
    Application service for operational actions.

    Coordinates human-facing farm actions.
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository



    def create_action(
        self,
        title: str,
        priority: str,
        assigned_to: str,
        source: str,
    ):

        action = OperationalAction(

            title=title,

            priority=priority,

            assigned_to=assigned_to,

            source=source,

        )


        return self.repository.save(
            action
        )



    def open_actions(
        self,
    ):

        return self.repository.open_actions()



    def complete_action(
        self,
        action_id: str,
    ):

        action = self.repository.get(
            action_id
        )


        if action is None:
            return None


        action.complete()


        return self.repository.save(
            action
        )
