from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass
class MilkTrace:
    trace_id: UUID
    animal_id: UUID
    milking_time: datetime
    volume_liters: float
    tank_id: UUID
    delivery_id: UUID | None = None
    created_at: datetime = datetime.utcnow()
