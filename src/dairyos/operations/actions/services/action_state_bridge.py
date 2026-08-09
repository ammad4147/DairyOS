from typing import List

from ..models.operational_action import OperationalAction

from dairyos.farm.operations.state.farm_operational_state import (
    FarmOperationalState,
)


class ActionStateBridge:
    """
    Projects operational action lifecycle
    into Farm Operational State.

    This bridge provides visibility only.
    Action lifecycle remains owned by
    OperationalActionService.
    """



    def _task_payload(
        self,
        action: OperationalAction,
    ) -> dict:

        return {

            "action_id":
                action.action_id,

            "title":
                action.title,

            "description":
                action.description,

            "assigned_to":
                action.assignment.assigned_to,

            "department":
                action.assignment.department,

            "status":
                action.status.status,

            "priority":
                action.priority,

            "source_event_id":
                action.source_event_id,

            "created_at":
                action.created_at,

            "due_date":
                action.due_date,

        }



    def sync_to_state(
        self,
        state: FarmOperationalState,
        actions: List[OperationalAction],
    ) -> FarmOperationalState:


        for action in actions:

            task = self._task_payload(
                action
            )


            if action.status.status in [
                "COMPLETED",
                "VERIFIED",
                "CLOSED",
            ]:

                state.record_completed_task(
                    task
                )

            else:

                state.record_open_task(
                    task
                )


        return state
