from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Index, Integer, String, Text, text

from ..database.base import Base
from dairyos.core.time_utils import utcnow


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
    created_at = Column(DateTime, default=utcnow, nullable=False)

    # Daily TMR snapshots are immutable authorities and must be exactly-once
    # per operational date even when two schedulers race.
    __table_args__ = (
        Index(
            "uq_tmr_daily_cost_snapshot_date",
            "animal_group",
            "effective_date",
            unique=True,
            postgresql_where=text(
                "animal_group = 'TMR_DAILY_COST_SNAPSHOT'"
            ),
            sqlite_where=text(
                "animal_group = 'TMR_DAILY_COST_SNAPSHOT'"
            ),
        ),
    )
