from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

@dataclass
class FeedInventory:
    feed_id: UUID
    name: str
    quantity_kg: float
    unit_cost_per_kg: float
    last_updated: datetime = datetime.utcnow()

    def add_stock(self, amount: float):
        self.quantity_kg += amount
        self.last_updated = datetime.utcnow()

    def consume(self, amount: float):
        if amount > self.quantity_kg:
            raise ValueError("Insufficient stock")
        self.quantity_kg -= amount
        self.last_updated = datetime.utcnow()
