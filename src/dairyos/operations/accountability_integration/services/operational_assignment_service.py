from dairyos.operations.accountability_integration.models.operational_assignment import (
    OperationalAssignment,
)


class OperationalAssignmentService:
    """
    Bridges operational users and operational actions.
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository



    def assign_action(
        self,
        user_id: str,
        action_id: str,
    ):

        assignment = OperationalAssignment(

            user_id=user_id,

            action_id=action_id,

        )


        return self.repository.save(
            assignment
        )



    def get_user_assignments(
        self,
        user_id: str,
    ):

        return (
            self.repository.by_user(
                user_id
            )
        )
