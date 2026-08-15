from datetime import date

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class Equipment(Base):
    """Canonical persisted equipment master record.

    The existing FarmOperationalState.equipment_status structure remains a
    derived operational projection. This table is the authoritative equipment
    identity/lifecycle record.
    """

    __tablename__ = "equipment"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    equipment_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    name = Column(
        String(200),
        nullable=False,
    )

    category = Column(
        String(100),
        nullable=False,
    )

    farm_id = Column(
        String(100),
        nullable=False,
        default="DEFAULT",
        index=True,
    )

    location = Column(
        String(200),
        nullable=True,
    )

    status = Column(
        String(50),
        nullable=False,
        default="AVAILABLE",
    )

    condition = Column(
        String(50),
        nullable=False,
        default="GOOD",
    )

    running_hours = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    commissioned_at = Column(
        DateTime,
        nullable=True,
    )

    last_service_at = Column(
        DateTime,
        nullable=True,
    )

    next_service_due_at = Column(
        DateTime,
        nullable=True,
        index=True,
    )

    active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=utcnow,
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )


class EquipmentServiceEvent(Base):
    """Immutable operational history for one equipment asset."""

    __tablename__ = "equipment_service_events"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    equipment_id = Column(
        String(100),
        ForeignKey(
            "equipment.equipment_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    event_date = Column(
        Date,
        nullable=False,
        default=lambda: utcnow().date(),
        index=True,
    )

    event_type = Column(
        String(100),
        nullable=False,
    )

    running_hours = Column(
        Float,
        nullable=True,
    )

    status_before = Column(
        String(50),
        nullable=True,
    )

    status_after = Column(
        String(50),
        nullable=True,
    )

    operator = Column(
        String(200),
        nullable=True,
    )

    notes = Column(
        String,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=utcnow,
    )
