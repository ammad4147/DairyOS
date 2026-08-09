from dataclasses import dataclass
from datetime import datetime


@dataclass
class AnimalHealthEvent:

    animal_id: str

    event_type: str

    description: str

    source: str

    event_date: datetime

    severity: str
