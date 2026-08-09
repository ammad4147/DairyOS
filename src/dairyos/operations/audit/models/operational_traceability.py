from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class OperationalTraceability:
    """
    Represents operational lineage.

    Links operational records through the lifecycle:

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


    This is an audit record only.
    It does not execute operations.
    """

    trace_id: str

    event_reference: str | None = None

    decision_reference: str | None = None

    action_reference: str | None = None

    execution_reference: str | None = None

    closure_reference: str | None = None

    created_at: datetime = (
        datetime.now(timezone.utc)
    )
