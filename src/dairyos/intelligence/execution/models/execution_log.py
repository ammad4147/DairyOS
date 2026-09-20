from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class ExecutionLog:
    """
    Represents an execution audit record.

    Future extensions:

    - distributed tracing
    - event sourcing
    - observability
    """

    workflow_type: str

    message: str

    recorded_by: str

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
