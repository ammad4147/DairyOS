from dataclasses import dataclass



@dataclass
class FeedInventory:


    feed_item: str

    available_quantity: float

    daily_consumption: float

    coverage_days: float

    status: str

    action: str
