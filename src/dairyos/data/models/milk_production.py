from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from ..database.base import Base


class MilkProduction(Base):


    __tablename__ = "milk_production"


    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )


    animal_id = Column(
        String,
        nullable=False
    )


    production_date = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )


    # The selected milking session is now persisted with the production
    # record.  It is nullable only for legacy rows created before G3.1;
    # all new API writes require a governed session value.
    milking_session = Column(
        String,
        nullable=True
    )


    morning_yield = Column(
        Float,
        default=0.0
    )


    afternoon_yield = Column(
        Float,
        default=0.0
    )


    evening_yield = Column(
        Float,
        default=0.0
    )


    total_yield = Column(
        Float,
        default=0.0
    )


    status = Column(
        String,
        default="RECORDED"
    )


    def calculate_total(self):

        self.total_yield = (
            self.morning_yield +
            self.afternoon_yield +
            self.evening_yield
        )

        return self.total_yield
