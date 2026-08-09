from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class WorkforceOwnershipSnapshot:
    """
    Represents workforce ownership intelligence.

    Indicates whether operational responsibilities
    are being owned and closed.
    """


    total_responsibilities: int


    completed_responsibilities: int


    pending_responsibilities: int


    ownership_score: float


    ownership_status: str


    escalation_required: bool


    generated_at: datetime = field(
        default_factory=lambda:
        datetime.now(timezone.utc)
    )
