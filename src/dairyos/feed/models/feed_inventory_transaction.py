from dataclasses import dataclass
from datetime import datetime


@dataclass
class FeedInventoryTransaction:

    transaction_id: str
    feed_id: str
    transaction_type: str
    quantity: float
    recorded_by: str
    timestamp: datetime | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
