from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

@dataclass
class Tank:
    tank_id: UUID
    capacity_liters: float
    current_volume_liters: float = 0.0
    created_at: datetime = datetime.utcnow()
