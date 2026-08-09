from dataclasses import dataclass
from datetime import datetime


@dataclass
class ClinicalHistory:

    animal_id: str

    complaint: str

    previous_conditions: str

    previous_treatments: str

    reproductive_history: str

    feeding_history: str

    created_by: str

    created_at: datetime
