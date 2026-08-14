from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
)

from datetime import datetime

from ..database.base import Base
from dairyos.core.time_utils import utcnow


class HealthObservation(Base):

    __tablename__ = "health_observation"


    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )


    animal_id = Column(
        String,
        nullable=False,
    )


    observed_at = Column(
        DateTime,
        default=utcnow,
        nullable=False,
    )


    #
    # Operational health fields
    #

    observation = Column(
        String,
        nullable=True,
    )


    reported_by = Column(
        String,
        nullable=True,
    )


    temperature = Column(
        Float,
        nullable=True,
    )


    #
    # Existing compatibility fields
    #

    symptom = Column(
        String,
        nullable=True,
    )


    temperature_c = Column(
        Float,
        nullable=True,
    )


    observer = Column(
        String,
        nullable=True,
    )


    notes = Column(
        String,
        nullable=True,
    )


    severity = Column(
        String,
        default="NORMAL",
    )


    status = Column(
        String,
        default="OPEN",
    )

    # Nullable link to a HealthCase (G5.1, 2026-08-14). An observation can
    # still be recorded standalone (unlinked) exactly as before -- this is
    # additive, not a required field on the existing write path.
    health_case_id = Column(
        Integer,
        nullable=True,
    )

    @property
    def effective_observation(self) -> str | None:
        return self.observation or self.symptom

    @property
    def effective_temperature(self) -> float | None:
        return self.temperature if self.temperature is not None else self.temperature_c

    @property
    def effective_reporter(self) -> str | None:
        return self.reported_by or self.observer
