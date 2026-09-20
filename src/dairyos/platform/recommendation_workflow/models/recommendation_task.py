from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class RecommendationTask:

    recommendation_id: str

    title: str

    assigned_to: str

    status: str

    created_at: datetime = datetime.now(
        UTC
    )

