from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

@dataclass
class Calf:
    calf_id: UUID
    birth_date: datetime
    birth_weight: float
    colostrum_received: bool = False
    weaning_date: datetime | None = None
    health_events: list = None

    def __post_init__(self):
        if self.health_events is None:
            self.health_events = []
