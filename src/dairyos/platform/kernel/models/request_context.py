from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class RequestContext:
    """
    Represents execution context for
    service/API/workflow operations.
    """

    request_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    actor_id: str = ""

    source: str = ""

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
