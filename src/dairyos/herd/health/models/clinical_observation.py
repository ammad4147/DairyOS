from dataclasses import dataclass
from datetime import datetime


@dataclass
class ClinicalObservation:

    animal_id: str

    observation_type: str

    observation_value: str

    severity: str

    observed_by: str

    observed_at: datetime

    notes: str
