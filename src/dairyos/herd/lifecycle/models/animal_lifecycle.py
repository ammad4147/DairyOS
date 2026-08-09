from dataclasses import dataclass



@dataclass
class AnimalLifecycle:


    animal_id: str

    age_months: int

    stage: str

    priority: str

    required_actions: list
