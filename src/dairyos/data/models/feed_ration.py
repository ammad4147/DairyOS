from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from ..database.base import Base


class FeedRation(Base):
    """Persisted ration formulation and nutrition targets."""

    __tablename__ = "feed_ration"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    animal_group = Column(String, nullable=False)
    ingredients_json = Column(Text, nullable=False)
    target_dmi_kg = Column(Float, nullable=True)
    dry_matter_pct = Column(Float, nullable=True)
    crude_protein_pct = Column(Float, nullable=True)
    ndf_pct = Column(Float, nullable=True)
    energy_mcal_kg = Column(Float, nullable=True)
    cost_per_kg = Column(Float, nullable=True)
    effective_date = Column(String, nullable=False)
    operator = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
