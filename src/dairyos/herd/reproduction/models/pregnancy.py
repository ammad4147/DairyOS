from dataclasses import dataclass
from datetime import date



@dataclass
class Pregnancy:


    animal_id: str

    confirmed_date: date

    expected_calving_date: date

    status: str
