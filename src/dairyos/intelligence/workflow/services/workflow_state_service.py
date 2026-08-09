from dairyos.intelligence.workflow.models.workflow_state import (
    WorkflowState,
)


class WorkflowStateService:
    """
    Manages workflow state transitions.
    """

    def update(
        self,
        workflow_type: str,
        current_state: str,
        previous_state: str,
    ) -> WorkflowState:

        return WorkflowState(
            workflow_type=workflow_type,
            current_state=current_state,
            previous_state=previous_state,
        )
