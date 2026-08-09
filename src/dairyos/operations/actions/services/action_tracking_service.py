from typing import List

from ..models.operational_action import OperationalAction


class ActionTrackingService:
    """
    Tracks operational action progress.

    Status changes are controlled through the
    ActionStatus lifecycle engine.
    """

    def update_status(
        self,
        action: OperationalAction,
        status: str,
    ) -> OperationalAction:

        action.status.transition_to(
            status.upper()
        )

        return action


    def active_actions(
        self,
        actions: List[OperationalAction],
    ) -> List[OperationalAction]:

        return [
            action
            for action in actions
            if action.status.status not in [
                "COMPLETED",
                "VERIFIED",
                "CLOSED",
            ]
        ]
