from dataclasses import dataclass
from datetime import datetime


@dataclass
class FeedingRecord:

    record_id: str
    animal_group: str
    feed_id: str
    quantity: float
    feeding_time: datetime
    worker: str
    supervisor_verified: bool = False
