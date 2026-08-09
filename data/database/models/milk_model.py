from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Uuid
from dairyos.data.database.session import Base

class MilkProductionORM(Base):
    __tablename__ = "milk_production"

    id = Column(Uuid(as_uuid=True), primary_key=True)
    animal_id = Column(Uuid(as_uuid=True), index=True, nullable=False)
    yield_liters = Column(Float, nullable=False)
    milking_time = Column(DateTime, nullable=False)
    operator_id = Column(Uuid(as_uuid=True), nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
