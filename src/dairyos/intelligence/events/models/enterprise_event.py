from dataclasses import dataclass, field
from datetime import datetime, UTC
from uuid import uuid4


@dataclass
class EnterpriseEvent:
    """
    Enterprise event envelope.

    Provides a common event identity boundary
    across DairyOS intelligence domains.

    Supports:

    - audit traceability
    - correlation tracking
    - subsystem interoperability
    - future event sourcing
    """

    event_type: str

    source: str

    actor: str

    entity_type: str

    entity_id: str

    payload: dict

    severity: str = "normal"

    event_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    correlation_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
