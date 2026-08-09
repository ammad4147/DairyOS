from dataclasses import dataclass


@dataclass
class Breed:


    name: str

    category: str

    expected_milk_per_day: float

    maturity_months: int

    active: bool = True
