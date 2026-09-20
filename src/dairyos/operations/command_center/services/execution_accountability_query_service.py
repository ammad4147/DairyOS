

class ExecutionAccountabilityQueryService:
    """
    Provides execution accountability
    read-side information for Command Center.

    Projection only.

    Does not:
    - create execution records
    - modify accountability records
    - complete operational work
    """


    def build_projection(
        self,
        records: list | None = None,
    ):

        records = (
            records
            if records is not None
            else []
        )


        completed = sum(

            1

            for record in records

            if record.status == "COMPLETED"

        )


        return {

            "execution_accountability_count":
                len(records),

            "completed_execution_count":
                completed,

            "pending_execution_count":
                (
                    len(records)
                    - completed
                ),

            "execution_accountability_records":
                records,

        }
