from dataclasses import dataclass
from datetime import date

from .status import AnimalStatus



@dataclass
class Animal:

    animal_id: str

    ear_tag: str

    breed: str

    gender: str

    birth_date: date

    status: AnimalStatus

    location: str
