from typing import List


class ExecutionAccountabilityProjection:
    """
    Builds Command Center visibility
    from execution accountability records.

    Read-side projection only.

    Does not:
    - create executions
    - modify accountability
    - close tasks
    """


    def __init__(
        self,
        records: List | None = None,
    ):

        self.records = (
            records
            if records is not None
            else []
        )


    def build(
        self,
    ):

        total = len(self.records)


        completed = len(

            [
                record

                for record in self.records

                if record.status == "COMPLETED"

            ]

        )


        pending = total - completed


        return {

            "total_assignments": total,

            "completed_assignments": completed,

            "pending_assignments": pending,

            "accountability_records": self.records,

        }
