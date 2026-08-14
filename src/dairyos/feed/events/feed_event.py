from dataclasses import dataclass
from datetime import datetime
from dairyos.core.time_utils import utcnow


@dataclass
class FeedEvent:

    event_id: str
    event_type: str
    feed_id: str
    quantity: float
    actor: str
    timestamp: datetime | None = None


    def __post_init__(self):

        if self.timestamp is None:
            self.timestamp = utcnow()
