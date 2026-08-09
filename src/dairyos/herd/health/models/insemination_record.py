from dataclasses import dataclass
from datetime import date


@dataclass
class InseminationRecord:

    animal_id: str

    insemination_date: date

    semen_type: str

    sire_id: str

    technician: str

    service_number: int

    pregnancy_result: str

    failure_reason: str
