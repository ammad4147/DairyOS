
from ..models.operational_traceability import (
    OperationalTraceability,
)


class OperationalTraceabilityService:
    """
    Maintains operational traceability records.

    Traceability connects:
        event
            |
            v
        decision
            |
            v
        action
            |
            v
        execution
            |
            v
        closure

    This service records lineage only.
    It does not execute operations
    or mutate operational state.
    """


    def __init__(self):

        self.records: list[
            OperationalTraceability
        ] = []



    def register_trace(
        self,
        record: OperationalTraceability,
    ) -> OperationalTraceability:

        self.records.append(
            record
        )

        return record



    def get_traces(
        self,
    ) -> list[OperationalTraceability]:

        return list(
            self.records
        )
