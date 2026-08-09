from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

@dataclass
class Delivery:
    delivery_id: UUID
    tank_id: UUID
    destination: str
    departure_time: datetime
    arrival_time: datetime | None = None
    created_at: datetime = datetime.utcnow()
