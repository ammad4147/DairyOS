from dataclasses import dataclass
from datetime import datetime


@dataclass
class HealthFollowUp:

    animal_id: str

    alert_id: str

    action_required: str

    responsible_person: str

    due_date: datetime

    completed: bool
