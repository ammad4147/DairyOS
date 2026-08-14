from dataclasses import dataclass
from datetime import datetime
from dairyos.core.time_utils import utcnow


@dataclass
class IntelligenceOutcome:
    """
    Standard intelligence kernel output object.
    """

    signal_name: str
    priority: str
    status: str
    recommendation: str
    created_at: datetime

    @classmethod
    def create(
        cls,
        signal_name: str,
        priority: str,
        recommendation: str,
    ):
        return cls(
            signal_name=signal_name,
            priority=priority,
            status="generated",
            recommendation=recommendation,
            created_at=utcnow(),
        )
