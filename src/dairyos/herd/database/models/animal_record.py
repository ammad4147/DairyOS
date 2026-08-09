from dataclasses import dataclass
from datetime import date



@dataclass
class AnimalRecord:


    animal_id: str

    ear_tag: str

    breed: str

    gender: str

    birth_date: date

    status: str

    location: str
