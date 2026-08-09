from dataclasses import dataclass
from datetime import datetime, UTC



@dataclass
class FeedRecord:
    """
    Represents a daily feed consumption entry.

    Created from actual feeding activity.
    """


    record_id: str

    feed_type: str

    quantity_kg: float

    cost_per_kg: float

    animal_group: str

    recorded_by: str

    recorded_at: datetime = (
        datetime.now(UTC)
    )
