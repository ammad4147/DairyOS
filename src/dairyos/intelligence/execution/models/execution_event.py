from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class ExecutionEvent:
    """
    Represents an execution lifecycle event.

    Records state movement for audit,
    observability, and future event sourcing.
    """

    workflow_type: str

    previous_status: str

    current_status: str

    triggered_by: str

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
