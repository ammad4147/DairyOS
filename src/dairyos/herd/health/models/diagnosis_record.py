from dataclasses import dataclass
from datetime import datetime


@dataclass
class DiagnosisRecord:

    animal_id: str

    diagnosis: str

    diagnosis_type: str

    confidence: str

    diagnosed_by: str

    notes: str

    diagnosed_at: datetime
