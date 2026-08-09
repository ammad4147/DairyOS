from dataclasses import dataclass
from datetime import datetime


@dataclass
class TreatmentPlan:

    animal_id: str

    diagnosis: str

    treatment: str

    dosage_instruction: str

    start_date: datetime

    duration: str

    responsible_person: str

    status: str
