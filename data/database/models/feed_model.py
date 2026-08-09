from datetime import datetime
from sqlalchemy import Column, DateTime, Float, String, Uuid
from dairyos.data.database.session import Base

class FeedStockORM(Base):
    __tablename__ = "feed_stock"

    id = Column(Uuid(as_uuid=True), primary_key=True)
    item_name = Column(String(100), nullable=False, unique=True)
    quantity_kg = Column(Float, nullable=False)
    reorder_threshold = Column(Float, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
