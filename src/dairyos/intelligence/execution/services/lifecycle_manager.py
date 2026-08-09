from dairyos.intelligence.execution.models.execution_event import (
    ExecutionEvent,
)

from dairyos.intelligence.execution.models.execution_lifecycle import (
    ExecutionLifecycle,
)


class LifecycleManager:
    """
    Controls execution state transitions.
    """

    TRANSITIONS = {

        "planned": [
            "assigned",
        ],

        "assigned": [
            "queued",
        ],

        "queued": [
            "started",
        ],

        "started": [
            "completed",
            "failed",
        ],

        "completed": [
            "verified",
        ],

        "verified": [
            "closed",
        ],

        "failed": [
            "escalated",
        ],

        "escalated": [
            "closed",
        ],
    }


    def transition(
        self,
        workflow_type: str,
        current_state: str,
        new_state: str,
        triggered_by: str,
    ):

        allowed = self.TRANSITIONS.get(
            current_state,
            [],
        )


        if new_state not in allowed:

            raise ValueError(
                f"Invalid transition: "
                f"{current_state} -> {new_state}"
            )


        lifecycle = ExecutionLifecycle(
            workflow_type=workflow_type,
            previous_state=current_state,
            current_state=new_state,
        )


        event = ExecutionEvent(
            workflow_type=workflow_type,
            previous_status=current_state,
            current_status=new_state,
            triggered_by=triggered_by,
        )


        return {
            "lifecycle": lifecycle,
            "event": event,
        }
