from dataclasses import dataclass, field
from uuid import UUID
from datetime import datetime
from dairyos.core.time_utils import utcnow

@dataclass
class Delivery:
    delivery_id: UUID
    tank_id: UUID
    destination: str
    departure_time: datetime
    arrival_time: datetime | None = None
    created_at: datetime = field(default_factory=utcnow)