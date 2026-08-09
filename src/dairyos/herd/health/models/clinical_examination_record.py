from dataclasses import dataclass
from datetime import datetime


@dataclass
class ClinicalExaminationRecord:

    animal_id: str

    veterinarian: str

    examination_type: str

    findings: list

    temperature: float

    notes: str

    examination_date: datetime
