from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class OperationalException:
    """
    Records operational deviations.

    Exceptions represent reality gaps.
    They do not block operations.

    DairyOS observes, records and
    supports recovery.
    """

    exception_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    category: str = ""

    description: str = ""

    severity: str = "low"

    source: str = ""

    status: str = "open"

    created_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    resolved_at: datetime | None = None


    def resolve(
        self,
    ):

        self.status = "resolved"

        self.resolved_at = (
            datetime.now(
                timezone.utc
            )
        )
