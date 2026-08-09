from dataclasses import dataclass
from datetime import date


@dataclass
class VaccinationHistory:

    animal_id: str

    vaccine_name: str

    vaccination_date: date

    next_due_date: date

    source: str

    verified: bool
