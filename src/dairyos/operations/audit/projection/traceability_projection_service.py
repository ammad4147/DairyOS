from typing import List

from dairyos.operations.audit.models.operational_traceability import (
    OperationalTraceability,
)


class TraceabilityProjectionService:
    """
    Builds read-only traceability projections.

    Projection:

        Event
          |
          v
        Decision
          |
          v
        Action
          |
          v
        Execution
          |
          v
        Closure


    This service:
        - exposes lineage visibility
        - supports Command Center views

    This service does not:
        - create records
        - mutate operational state
        - execute actions
    """


    def __init__(self):

        self.records: List[
            OperationalTraceability
        ] = []



    def register(
        self,
        record: OperationalTraceability,
    ) -> OperationalTraceability:

        self.records.append(
            record
        )

        return record



    def build_projection(
        self,
    ) -> dict:

        return {

            "total": len(
                self.records
            ),

            "traces": [

                {

                    "trace_id":
                        item.trace_id,

                    "event":
                        item.event_reference,

                    "decision":
                        item.decision_reference,

                    "action":
                        item.action_reference,

                    "execution":
                        item.execution_reference,

                    "closure":
                        item.closure_reference,

                }

                for item in self.records

            ],

        }
