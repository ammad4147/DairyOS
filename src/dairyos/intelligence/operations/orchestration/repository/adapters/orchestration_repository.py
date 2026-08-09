from dairyos.intelligence.operations.orchestration.models.operational_action import (
    OperationalAction,
)


class OrchestrationRepository:
    """
    Repository adapter for operational orchestration objects.

    Future extensions:

    - database persistence
    - audit history
    - event sourcing
    - execution analytics
    """

    def __init__(self):
        self._actions = []


    def save_action(
        self,
        action: OperationalAction,
    ) -> OperationalAction:

        self._actions.append(action)

        return action


    def get_actions(self):

        return list(self._actions)


    def count_actions(self) -> int:

        return len(self._actions)
