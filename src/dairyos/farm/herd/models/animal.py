from dataclasses import dataclass
from datetime import date



@dataclass
class Animal:
    """
    Represents an individual dairy animal.

    This is the foundation entity
    for herd management.
    """


    animal_id: str

    tag_number: str

    breed: str

    gender: str

    birth_date: date

    status: str

    lactation_number: int = 0

    is_milking: bool = False
