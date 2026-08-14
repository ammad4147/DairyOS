from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
from dairyos.core.time_utils import utcnow

@dataclass
class MilkTrace:
    trace_id: UUID
    animal_id: UUID
    milking_time: datetime
    volume_liters: float
    tank_id: UUID
    delivery_id: UUID | None = None
    created_at: datetime = field(default_factory=utcnow)