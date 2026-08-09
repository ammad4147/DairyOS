from dataclasses import dataclass
from datetime import datetime, timezone



@dataclass
class RecommendationTask:

    recommendation_id: str

    title: str

    assigned_to: str

    status: str

    created_at: datetime = datetime.now(
        timezone.utc
    )

