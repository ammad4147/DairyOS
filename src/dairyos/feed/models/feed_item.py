from dataclasses import dataclass


@dataclass
class FeedItem:

    feed_id: str
    name: str
    category: str
    unit: str
    current_stock: float = 0
    minimum_stock_level: float = 0
    supplier: str | None = None
    active: bool = True
