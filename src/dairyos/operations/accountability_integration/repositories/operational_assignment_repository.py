class OperationalAssignmentRepository:
    """
    Stores operational accountability assignments.
    """


    def __init__(
        self,
    ):

        self._assignments = {}



    def save(
        self,
        assignment,
    ):

        self._assignments[
            assignment.assignment_id
        ] = assignment


        return assignment



    def get(
        self,
        assignment_id,
    ):

        return self._assignments.get(
            assignment_id
        )



    def by_user(
        self,
        user_id,
    ):

        return [

            assignment

            for assignment in self._assignments.values()

            if assignment.user_id == user_id

        ]



    def by_action(
        self,
        action_id,
    ):

        return [

            assignment

            for assignment in self._assignments.values()

            if assignment.action_id == action_id

        ]
