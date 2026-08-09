from dataclasses import dataclass



@dataclass
class FeedManagement:


    animal_group: str

    animal_count: int

    daily_feed_kg: float

    daily_feed_cost: float

    cost_per_animal: float

    status: str
