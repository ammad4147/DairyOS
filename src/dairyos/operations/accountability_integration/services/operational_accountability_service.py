from dairyos.operations.accountability_integration.models.execution_accountability import (
    ExecutionAccountability,
)


class OperationalAccountabilityService:
    """
    Converts operational assignments
    into accountability records.
    """


    def __init__(
        self,
    ):

        self.records = []



    def create_from_assignment(
        self,
        assignment,
        action,
        user,
    ):

        record = ExecutionAccountability(

            execution_id=(
                assignment.assignment_id
            ),

            staff_member=(
                user.user_id
            ),

            task_name=(
                action.title
            ),

        )


        self.records.append(
            record
        )


        return record



    def complete_accountability(
        self,
        execution_id: str,
    ):

        for record in self.records:

            if record.execution_id == execution_id:

                record.complete()

                return record


        return None



    def get_records(
        self,
    ):

        return self.records
