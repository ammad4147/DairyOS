from dataclasses import dataclass, field
from datetime import datetime, UTC
from uuid import uuid4


@dataclass
class FarmDay:
    """
    Represents one operational farm day.

    A farm day is the container
    for all activities performed
    during daily operations.
    """

    farm_id: str

    operational_date: str

    status: str = "open"

    day_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    started_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    closed_at: datetime | None = None

    activities: list = field(
        default_factory=list
    )


    def add_activity(
        self,
        activity,
    ):

        self.activities.append(
            activity
        )


    def close(
        self,
    ):

        self.status = "closed"

        self.closed_at = (
            datetime.now(UTC)
        )
