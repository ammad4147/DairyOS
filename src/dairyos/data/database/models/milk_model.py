from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey
from dairyos.data.database.session import Base
from dairyos.core.time_utils import utcnow


class MilkProductionORM(Base):
    __tablename__ = "milk_production_orm"

    id = Column(Integer, primary_key=True, index=True)
    animal_id = Column(String, ForeignKey("animal.animal_id"), index=True, nullable=False)
    quantity_liters = Column(Float, nullable=False)
    morning_yield = Column(Float, nullable=True)
    afternoon_yield = Column(Float, nullable=True)
    evening_yield = Column(Float, nullable=True)
    milking_session = Column(String, nullable=True)
    status = Column(String, default="RECORDED", nullable=False)
    recorded_at = Column(DateTime, default=utcnow, nullable=False)

    @property
    def cow_id(self) -> str:
        """Backward compatibility alias for cow_id."""
        return self.animal_id

    @cow_id.setter
    def cow_id(self, value: str):
        self.animal_id = value
