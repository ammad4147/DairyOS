from sqlalchemy import Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.sql import func

from dairyos.data.database.base import Base


class BreedingPropagationOutbox(Base):
    __tablename__ = "breeding_propagation_outbox"

    id = Column(Integer, primary_key=True, autoincrement=True)
    propagation_id = Column(String, nullable=False, unique=True, index=True)
    record_id = Column(String, nullable=False, index=True)
    animal_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String, nullable=False, default="PENDING", index=True)
    attempts = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    delivered_at = Column(DateTime, nullable=True)
