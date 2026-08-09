from dataclasses import dataclass
from datetime import datetime


@dataclass
class HealthAlert:

    animal_id: str

    alert_type: str

    severity: str

    description: str

    assigned_to: str

    status: str

    created_at: datetime
