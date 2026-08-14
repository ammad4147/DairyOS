from dataclasses import dataclass, field
from uuid import UUID
from datetime import datetime
from dairyos.core.time_utils import utcnow

@dataclass
class FeedInventory:
    feed_id: UUID
    name: str
    quantity_kg: float
    unit_cost_per_kg: float
    last_updated: datetime = field(default_factory=utcnow)
    def add_stock(self, amount: float):
        self.quantity_kg += amount
        self.last_updated = utcnow()

    def consume(self, amount: float):
        if amount > self.quantity_kg:
            raise ValueError("Insufficient stock")
        self.quantity_kg -= amount
        self.last_updated = utcnow()
