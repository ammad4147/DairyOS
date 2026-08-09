from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class OperationalShift:
    """
    Represents a farm operational shift.

    Shift state is intentionally lightweight.
    It records operational ownership rather
    than workflow execution.
    """

    shift_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    shift_name: str = ""

    supervisor: str = ""

    status: str = "open"

    started_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    closed_at: datetime | None = None

    transferred_actions: int = 0


    def close(
        self,
        transferred_actions: int = 0,
    ):

        self.status = "closed"

        self.transferred_actions = (
            transferred_actions
        )

        self.closed_at = (
            datetime.now(
                timezone.utc
            )
        )
