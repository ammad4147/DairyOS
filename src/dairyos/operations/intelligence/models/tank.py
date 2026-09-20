from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from dairyos.core.time_utils import utcnow


@dataclass
class Tank:
    tank_id: UUID
    capacity_liters: float
    current_volume_liters: float = 0.0
    created_at: datetime = field(default_factory=utcnow)