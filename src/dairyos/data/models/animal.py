from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class Animal(Base):
    """
    Persistent animal master record.

    Non-milking directives are animal/herd-state facts. They do not belong
    to the milk disposition domain.

    ``non_milking_directive`` determines whether the animal is currently
    outside the active milking herd.
    """

    __tablename__ = "animal"

    id = Column(Integer, primary_key=True, autoincrement=True)

    animal_id = Column(String, unique=True, nullable=False, index=True)

    # Historical identifier carried by an animal before it entered DairyOS.
    # It is retained for traceability and must never replace the permanent ID.
    legacy_animal_id = Column(String, unique=True, nullable=True, index=True)

    animal_type = Column(String, nullable=False)
    ear_tag = Column(String, nullable=True)
    rfid = Column(String, nullable=True)
    breed = Column(String, nullable=True)
    sex = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    date_of_acquisition = Column(Date, nullable=True)
    dam_id = Column(String, nullable=True)
    sire_id = Column(String, nullable=True)
    lifecycle_status = Column(String, nullable=True)
    status = Column(String, default="ACTIVE", nullable=False)
    is_currently_milking = Column(Boolean, default=False, nullable=False)
    milking_frequency = Column(String, nullable=True)
    production_group = Column(String, nullable=True)
    location = Column(String, nullable=True)
    active = Column(Boolean, default=True, nullable=False)

    # ------------------------------------------------------------------
    # Veterinary non-milking directive state
    # ------------------------------------------------------------------

    non_milking_directive = Column(
        String,
        nullable=False,
        default="NONE",
        server_default="NONE",
        index=True,
    )
    non_milking_since = Column(DateTime, nullable=True)
    non_milking_until = Column(DateTime, nullable=True)
    non_milking_reason = Column(String, nullable=True)
    non_milking_changed_by = Column(String, nullable=True)

    # Captures whether the animal belonged to the active milking herd
    # immediately before a non-milking directive was imposed.
    non_milking_restore_to_milking = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)

    def __init__(self, animal_id=None, animal_type=None, status=None, **kwargs):
        super().__init__(**kwargs)

        if animal_id is not None:
            self.animal_id = animal_id
        if animal_type is not None:
            self.animal_type = animal_type

        if status is not None:
            self.status = status
        elif self.status is None:
            self.status = "ACTIVE"

        if self.is_currently_milking is None:
            self.is_currently_milking = False
        if self.active is None:
            self.active = True
        if self.non_milking_directive is None:
            self.non_milking_directive = "NONE"
        if self.non_milking_restore_to_milking is None:
            self.non_milking_restore_to_milking = False

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
