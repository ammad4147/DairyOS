from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Date

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class CMPScenario(Base):
    """Persisted cost-of-milk-production scenario.

    Scenario records are analytical assumptions. They never modify financial
    transactions, milk production, or other authoritative operational facts.
    """

    __tablename__ = "cmp_scenarios"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    scenario_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    name = Column(
        String,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=utcnow,
        nullable=False,
    )

    created_by = Column(
        String,
        nullable=False,
    )

    period_start = Column(
        Date,
        nullable=False,
    )

    period_end = Column(
        Date,
        nullable=False,
    )

    currency = Column(
        String,
        default="PKR",
        nullable=False,
    )

    basis = Column(
        String,
        nullable=False,
        default="PERSISTED_ACTUALS",
    )

    selected_cost_domains = Column(
        JSON,
        nullable=False,
    )

    assumptions = Column(
        JSON,
        nullable=False,
    )

    milk_volume_litres = Column(
        Float,
        nullable=True,
    )

    eligible_cost = Column(
        Float,
        nullable=True,
    )

    cmp_per_litre = Column(
        Float,
        nullable=True,
    )

    status = Column(
        String,
        nullable=False,
        default="ACTIVE",
    )
