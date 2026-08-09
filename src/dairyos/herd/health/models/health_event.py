from dataclasses import dataclass
from datetime import datetime


@dataclass
class HealthEvent:

    animal_id: str

    event_type: str

    description: str

    severity: str

    reported_by: str

    status: str

    created_at: datetime
