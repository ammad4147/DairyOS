from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date
from datetime import datetime

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class Animal(Base):
    """
    Operational livestock master record — the atomic unit every other
    domain entity (milk, health, reproduction, finance) attaches to.

    Replaces the previous in-memory dataclass with a real, persistent
    model. Field names and semantics (status/active, activate/deactivate)
    are preserved from the original for compatibility; lifecycle_status
    and milking_frequency are new fields required to drive the
    measurement-schedule engine.
    """

    __tablename__ = "animal"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    animal_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    animal_type = Column(
        String,
        nullable=False
    )

    ear_tag = Column(
        String,
        nullable=True
    )

    rfid = Column(
        String,
        nullable=True
    )

    breed = Column(
        String,
        nullable=True
    )

    sex = Column(
        String,
        nullable=True
    )

    date_of_birth = Column(
        Date,
        nullable=True
    )

    dam_id = Column(
        String,
        nullable=True
    )

    sire_id = Column(
        String,
        nullable=True
    )

    # CALF, HEIFER, LACTATING, DRY, SOLD, DECEASED. Nullable at the
    # schema level (some construction paths, e.g. legacy direct
    # Animal(...) calls, don't set it) but required by the
    # animal_management API layer, which is the intended entry point
    # for real data — see VALID_LIFECYCLE_STATUSES in that router.
    lifecycle_status = Column(
        String,
        nullable=True
    )

    # Legacy free-text status field, kept for compatibility with
    # existing code/tests that reference it directly.
    status = Column(
        String,
        default="ACTIVE",
        nullable=False
    )

    is_currently_milking = Column(
        Boolean,
        default=False,
        nullable=False
    )

    # TWICE_DAILY or THRICE_DAILY — the CURRENT frequency, mirrored here
    # for fast lookups. The authoritative history lives in
    # AnimalMilkingScheduleHistory (see below).
    milking_frequency = Column(
        String,
        nullable=True
    )

    production_group = Column(
        String,
        nullable=True
    )

    location = Column(
        String,
        nullable=True
    )

    active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=utcnow,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=utcnow,
        nullable=False
    )

    def __init__(
        self,
        animal_id=None,
        animal_type=None,
        status=None,
        **kwargs,
    ):
        """
        Explicit constructor to preserve backward compatibility with
        existing code that constructs Animal(animal_id, animal_type,
        status) positionally, as the previous dataclass allowed.

        Also sets Python-side defaults for fields that have a
        database-level `default=` (active, lifecycle_status, status,
        created_at, updated_at). SQLAlchemy's Column(default=...) only
        applies at INSERT time; code that reads these attributes
        before the object is added to a session and committed would
        otherwise see None, which silently breaks the "active is
        True by default" contract the previous dataclass guaranteed
        immediately on construction.
        """

        super().__init__(**kwargs)

        if animal_id is not None:
            self.animal_id = animal_id

        if animal_type is not None:
            self.animal_type = animal_type

        if status is not None:
            self.status = status
        elif self.status is None:
            self.status = "ACTIVE"

        # lifecycle_status is intentionally NOT defaulted here.
        # Per the data model, a farm's animal classification should
        # be an explicit choice, not a silent default that could mask
        # a real data-entry omission. The API layer (animal_management
        # router) enforces this by requiring it on creation; this
        # model-level constructor simply doesn't second-guess that by
        # inventing a value when used directly (e.g. in tests that
        # construct Animal() without it).

        if self.is_currently_milking is None:
            self.is_currently_milking = False

        if self.active is None:
            self.active = True

        now = utcnow()

        if self.created_at is None:
            self.created_at = now

        if self.updated_at is None:
            self.updated_at = now

    def deactivate(self):

        self.active = False
        self.status = "INACTIVE"
        self.updated_at = utcnow()

    def activate(self):

        self.active = True
        self.status = "ACTIVE"
        self.updated_at = utcnow()
