from datetime import datetime

from ..models.feed_inventory_item import FeedInventoryItem
from dairyos.core.time_utils import utcnow


class FeedInventoryItemRepository:
    def __init__(self, session=None):
        self.session = session
        self.records = []

    def add(self, item: FeedInventoryItem):
        item.updated_at = utcnow()
        if self.session:
            self.session.add(item)
            self.session.commit()
            self.session.refresh(item)
            return item
        if getattr(item, "id", None) is None:
            item.id = len(self.records) + 1
        self.records.append(item)
        return item

    def get_all(self):
        if self.session:
            return self.session.query(FeedInventoryItem).order_by(FeedInventoryItem.item.asc()).all()
        return list(self.records)

    def get_by_id(self, item_id: int):
        if self.session:
            return self.session.query(FeedInventoryItem).filter(FeedInventoryItem.id == item_id).first()
        return next((row for row in self.records if row.id == item_id), None)

    def get_by_item(self, item: str):
        normalized = item.strip()
        if self.session:
            return self.session.query(FeedInventoryItem).filter(FeedInventoryItem.item == normalized).first()
        return next((row for row in self.records if row.item == normalized), None)

    def exists_item(self, item: str) -> bool:
        return self.get_by_item(item) is not None
