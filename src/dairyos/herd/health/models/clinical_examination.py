from dataclasses import dataclass
from datetime import datetime


@dataclass
class ClinicalExamination:

    animal_id: str

    temperature: str

    respiratory_rate: str

    heart_rate: str

    body_condition_score: str

    physical_findings: str

    examiner: str

    examined_at: datetime
