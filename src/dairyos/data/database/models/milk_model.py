from sqlalchemy import Column, Integer, Float, DateTime, String
from dairyos.data.database.session import Base
import datetime
from dairyos.core.time_utils import utcnow

class MilkProductionORM(Base):
    __tablename__ = "milk_production"

    id = Column(Integer, primary_key=True, index=True)
    cow_id = Column(String, index=True, nullable=False)
    quantity_liters = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=utcnow, nullable=False)
