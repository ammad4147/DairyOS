from dataclasses import dataclass
from datetime import date



@dataclass
class BreedingRecord:


    animal_id: str

    service_date: date

    breeding_method: str

    semen_type: str

    technician: str
