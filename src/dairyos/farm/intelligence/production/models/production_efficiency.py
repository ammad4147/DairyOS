from dataclasses import dataclass



@dataclass
class ProductionEfficiency:
    """
    Represents dairy production efficiency indicators.
    """


    milk_litres: float

    milking_animals: int

    feed_cost: float

    feed_cost_per_litre: float

    litres_per_animal: float

    efficiency_status: str
