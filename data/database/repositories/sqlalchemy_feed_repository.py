from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from dairyos.domain.feed.repository import FeedRepositoryInterface
from dairyos.domain.feed.entity import FeedStock
from dairyos.data.database.models.feed_model import FeedStockORM

class SQLAlchemyFeedRepository(FeedRepositoryInterface):
    def __init__(self, session: Session):
        self._session = session

    def add(self, stock: FeedStock) -> None:
        orm_model = FeedStockORM(
            id=stock.id,
            item_name=stock.item_name,
            quantity_kg=stock.quantity_kg,
            reorder_threshold=stock.reorder_threshold,
            last_updated=stock.last_updated
        )
        self._session.add(orm_model)

    def get_by_id(self, stock_id: UUID) -> Optional[FeedStock]:
        orm_model = self._session.query(FeedStockORM).filter_by(id=stock_id).first()
        if not orm_model:
            return None
        return FeedStock(
            id=orm_model.id,
            item_name=orm_model.item_name,
            quantity_kg=orm_model.quantity_kg,
            reorder_threshold=orm_model.reorder_threshold,
            last_updated=orm_model.last_updated
        )
