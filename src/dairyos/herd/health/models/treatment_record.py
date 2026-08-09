from dataclasses import dataclass
from datetime import datetime


@dataclass
class TreatmentRecord:

    animal_id: str

    diagnosis_reference: str

    treatment_type: str

    medication: str

    dosage: str

    veterinarian: str

    start_date: datetime

    status: str
