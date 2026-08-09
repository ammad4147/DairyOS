from dataclasses import dataclass



@dataclass
class ProductionEntity:

    record_id: str

    animal_id: str

    metric: str

    value: float

