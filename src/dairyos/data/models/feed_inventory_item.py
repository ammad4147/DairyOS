from sqlalchemy import Boolean, Column, Float, Integer, String

from ..database.base import Base
from dairyos.core.time_utils import utcnow
from sqlalchemy import DateTime


class FeedInventoryItem(Base):
    """Master data for feed stock controls; balance remains movement-derived."""

    __tablename__ = "feed_inventory_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item = Column(String, nullable=False, unique=True)
    category = Column(String, nullable=False, default="FEED")
    unit = Column(String, nullable=False, default="kg")
    location = Column(String, nullable=True)
    reorder_level = Column(Float, nullable=False, default=0.0)
    active = Column(Boolean, nullable=False, default=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)
