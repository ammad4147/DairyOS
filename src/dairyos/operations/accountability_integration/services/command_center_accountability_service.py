from typing import List

from ..models.execution_accountability import (
    ExecutionAccountability,
)


class CommandCenterAccountabilityService:
    """
    Provides accountability projections
    for Command Center views.

    This service does not create accountability.
    It only projects existing accountability records.

    Source of truth:

        OperationalExecution
                |
                v
        ExecutionAccountability
                |
                v
        Command Center Projection
    """


    def __init__(
        self,
    ):

        self.records: List[
            ExecutionAccountability
        ] = []



    def register_record(
        self,
        record: ExecutionAccountability,
    ) -> ExecutionAccountability:
        """
        Register an existing accountability record.

        Completion remains manual.
        """

        self.records.append(
            record
        )

        return record



    def get_accountability_view(
        self,
    ):

        total = len(
            self.records
        )


        completed = len(

            [
                record

                for record in self.records

                if record.status == "COMPLETED"

            ]

        )


        return {

            "assigned": total,

            "completed": completed,

            "pending": (
                total - completed
            ),

            "records": (
                self.records
            ),

        }



    def get_records(
        self,
    ) -> List[ExecutionAccountability]:

        return self.records
