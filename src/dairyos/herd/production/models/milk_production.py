from dataclasses import dataclass



@dataclass
class MilkProduction:


    animal_group: str

    animal_count: int

    expected_milk: float

    actual_milk: float

    variance: float

    status: str
