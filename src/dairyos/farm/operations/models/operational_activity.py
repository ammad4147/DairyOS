from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class OperationalActivity:
    """
    Represents live farm operational work.

    This model represents execution status,
    not a completed farm fact.

    Completed facts remain represented by:
    - MilkRecord
    - FeedRecord
    - HealthObservation
    - BreedingRecord

    Rules:
    - Manual operational activity remains authoritative.
    - Runtime controls lifecycle progression.
    - No prediction.
    - No autonomous execution.
    """

    activity_id: str

    activity_type: str

    status: str = "CREATED"

    assigned_to: str | None = None

    created_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc)
    )

    started_at: datetime | None = None

    completed_at: datetime | None = None

    verified_at: datetime | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


    def assign(
        self,
        operator: str,
    ):
        """
        Assign operational responsibility.
        """

        self.assigned_to = operator

        self.status = "ASSIGNED"

        return self



    def start(
        self,
    ):
        """
        Mark activity as started.
        """

        self.status = "IN_PROGRESS"

        self.started_at = (
            datetime.now(timezone.utc)
        )

        return self



    def complete(
        self,
    ):
        """
        Mark activity as completed.
        """

        self.status = "COMPLETED"

        self.completed_at = (
            datetime.now(timezone.utc)
        )

        return self



    def verify(
        self,
    ):
        """
        Mark activity as verified.
        """

        self.status = "VERIFIED"

        self.verified_at = (
            datetime.now(timezone.utc)
        )

        return self



    def is_active(
        self,
    ):
        """
        Indicates whether operational work
        is currently underway.
        """

        return self.status in (
            "ASSIGNED",
            "IN_PROGRESS",
        )



    def is_complete(
        self,
    ):
        """
        Indicates completion state.
        """

        return self.status in (
            "COMPLETED",
            "VERIFIED",
        )
