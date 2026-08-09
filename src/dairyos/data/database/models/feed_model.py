from sqlalchemy import Column, Integer, Float, String, DateTime
from dairyos.data.database.session import Base
import datetime

class FeedStockORM(Base):
    __tablename__ = "feed_stock"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, index=True, nullable=False)
    quantity_kg = Column(Float, nullable=False)
    last_restocked = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
