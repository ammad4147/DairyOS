from dataclasses import dataclass
from datetime import datetime, timezone



@dataclass
class FeedbackSignal:

    recommendation_id: str

    action_taken: str

    outcome: str

    effectiveness_score: float

    created_at: datetime = datetime.now(
        timezone.utc
    )

