from dataclasses import dataclass
from datetime import date



@dataclass
class HealthRecord:


    animal_id: str

    event_date: date

    diagnosis: str

    treatment: str

    veterinarian: str

    status: str
