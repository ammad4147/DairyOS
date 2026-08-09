from dataclasses import dataclass, field
from datetime import datetime, UTC
from uuid import uuid4


@dataclass
class FeedRecord:
    """
    Daily feed consumption record.

    Supports:

    - animal group feeding
    - operational feed tracking
    - feed cost analysis
    """

    animal_group: str | None = None

    group_name: str | None = None

    feed_type: str = ""

    quantity_kg: float = 0.0

    cost: float = 0.0

    operator: str = ""

    record_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self):
        if self.animal_group is None:
            self.animal_group = self.group_name
