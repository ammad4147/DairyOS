from dataclasses import dataclass



@dataclass
class FeedPlan:


    group_name: str

    silage_kg: float

    concentrate_kg: float

    mineral_grams: float
