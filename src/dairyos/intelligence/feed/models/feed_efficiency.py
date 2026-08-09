from dataclasses import dataclass



@dataclass
class FeedEfficiency:


    group_id: str

    feed_quantity: float

    milk_output: float

    efficiency: float

    status: str

    recommendation: str
