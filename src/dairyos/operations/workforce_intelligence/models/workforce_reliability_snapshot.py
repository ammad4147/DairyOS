from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class WorkforceReliabilitySnapshot:
    """
    Represents workforce execution reliability.

    Derived from measured operational
    execution behaviour only.
    """


    total_tasks: int


    completed_tasks: int


    pending_tasks: int


    completion_rate: float


    reliability_score: float


    reliability_status: str


    attention_required: bool


    generated_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )
