from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class IntelligenceRecommendation:
    """
    Represents an intelligence-driven recommended action.

    Recommendations guide decisions.
    They do not execute farm actions.
    """

    recommendation_type: str

    priority: str

    source_signal: str

    action: str

    reasoning: str = ""

    evidence: dict = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda:
        datetime.now(timezone.utc)
    )

