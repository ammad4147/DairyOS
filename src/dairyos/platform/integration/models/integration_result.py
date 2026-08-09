from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class IntegrationResult:
    """
    Result returned by enterprise integrations.
    """

    success: bool

    message: str = ""

    data: dict[str, Any] = field(
        default_factory=dict
    )

    completed_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
