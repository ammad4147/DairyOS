from dataclasses import dataclass



@dataclass
class AnimalHealth:


    animal_id: str

    condition: str

    severity: str

    priority: str

    required_actions: list
