from dairyos.operations.command_center.models.operational_action import (
    OperationalAction,
)



class OperationalActionRepository:
    """
    In-memory repository for farm operational actions.

    Stores human-facing action items.
    """


    def __init__(
        self,
    ):

        self._actions = {}



    def save(
        self,
        action: OperationalAction,
    ):

        self._actions[
            action.action_id
        ] = action


        return action



    def get(
        self,
        action_id: str,
    ):

        return self._actions.get(
            action_id
        )



    def all(
        self,
    ):

        return list(
            self._actions.values()
        )



    def open_actions(
        self,
    ):

        return [

            action

            for action in self._actions.values()

            if action.status == "open"

        ]



    def count(
        self,
    ):

        return len(
            self._actions
        )
