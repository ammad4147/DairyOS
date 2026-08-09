from typing import List

from ..models.operational_action import OperationalAction
from ..models.action_assignment import ActionAssignment
from ..models.action_status import ActionStatus


class OperationalActionService:
    """
    Creates and manages operational actions.

    Actions represent operational work commitments.
    """

    def __init__(self):

        self.actions: List[OperationalAction] = []


    def create_action(
        self,
        title: str,
        description: str,
        assigned_to: str,
        department: str,
        source_event_id: str | None = None,
        priority: str = "NORMAL",
        source_decision_id: str | None = None,
    ) -> OperationalAction:


        action = OperationalAction(

            action_id=f"ACT-{len(self.actions)+1:04d}",

            title=title,

            description=description,

            assignment=ActionAssignment(
                assigned_to=assigned_to,
                department=department,
            ),

            status=ActionStatus(
                status="OPEN",
            ),

            source_event_id=source_event_id,

            source_decision_id=source_decision_id,

            priority=priority.upper(),

            created_by_system=True,

        )


        self.actions.append(
            action
        )


        return action



    def open_action(
        self,
        action: OperationalAction,
    ) -> OperationalAction:

        if action.status.status == "CREATED":

            action.status.transition_to(
                "OPEN"
            )

        return action



    def get_actions(
        self,
    ) -> List[OperationalAction]:

        return self.actions
