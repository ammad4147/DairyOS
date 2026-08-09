from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class IntegrationRequest:
    """
    Enterprise platform integration request.

    Represents communication between
    DairyOS platform services.
    """

    source_service: str
    target_service: str
    action: str

    payload: dict[str, Any] = field(
        default_factory=dict
    )

    request_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
