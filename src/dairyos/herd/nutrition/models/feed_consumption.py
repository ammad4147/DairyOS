from dataclasses import dataclass
from datetime import date



@dataclass
class FeedConsumption:


    group_name: str

    consumption_date: date

    total_feed_kg: float

    animals_count: int
