from dairyos.intelligence.operations.orchestration.models.action_assignment import (
    ActionAssignment,
)


class AssignmentService:
    """
    Assigns operational actions
    to responsible personnel.
    """

    def assign(
        self,
        action_type: str,
        assigned_to: str,
        assigned_role: str,
    ) -> ActionAssignment:

        return ActionAssignment(
            action_type=action_type,
            assigned_to=assigned_to,
            assigned_role=assigned_role,
            status="assigned",
        )
