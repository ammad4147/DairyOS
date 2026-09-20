
from ..models.execution_accountability import (
    ExecutionAccountability,
)


class AccountabilityBridge:
    """
    Converts operational execution
    into staff accountability records.
    """


    def __init__(self):

        self.records: list[
            ExecutionAccountability
        ] = []


    def create_accountability_record(
        self,
        execution,
        task_name: str,
    ) -> ExecutionAccountability:


        record = ExecutionAccountability(

            execution_id=execution.execution_id,

            staff_member=execution.assigned_to,

            task_name=task_name,

        )


        self.records.append(record)


        return record



    def get_records(
        self,
    ) -> list[ExecutionAccountability]:

        return self.records
