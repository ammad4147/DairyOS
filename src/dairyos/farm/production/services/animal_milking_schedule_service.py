"""Authoritative animal milking-schedule interpretation service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


FREQUENCY_SESSIONS: dict[str, tuple[str, ...]] = {
    "TWICE_DAILY": ("MORNING", "EVENING"),
    "THRICE_DAILY": ("MORNING", "AFTERNOON", "EVENING"),
}


@dataclass(frozen=True)
class MilkingScheduleSnapshot:
    """Resolved schedule state for one animal and operational date."""

    animal_id: str
    operational_date: date
    milking_frequency: str | None
    expected_sessions: tuple[str, ...]
    source: str
    history_id: int | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    changed_by: str | None = None
    reason: str | None = None


class AnimalMilkingScheduleService:
    """Resolve animal-specific milking schedules without frontend inference."""

    def __init__(self, animal_repository):
        self.animal_repository = animal_repository

    @staticmethod
    def _as_date(value: date | datetime) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        raise TypeError("operational_date must be a date or datetime")

    @staticmethod
    def sessions_for_frequency(frequency: str | None) -> tuple[str, ...]:
        if frequency is None:
            return ()
        return FREQUENCY_SESSIONS.get(str(frequency).strip().upper(), ())

    def _matching_history(self, animal_id: str, operational_date: date):
        history = self.animal_repository.get_milking_frequency_history(animal_id)
        for record in history:
            effective_from = getattr(record, "effective_from", None)
            effective_to = getattr(record, "effective_to", None)
            if effective_from is None:
                continue
            from_date = self._as_date(effective_from)
            to_date = self._as_date(effective_to) if effective_to else None
            if from_date <= operational_date and (
                to_date is None or operational_date < to_date
            ):
                return record
        return None

    def get_frequency_for_date(
        self, animal: Any, operational_date: date | datetime
    ) -> str | None:
        """Return the frequency effective for an animal on an operational date.

        If schedule history exists, historical resolution never falls back to
        the current Animal frequency. Current-frequency fallback is retained
        only for animals that have no history at all.
        """
        op_date = self._as_date(operational_date)
        animal_id = getattr(animal, "animal_id", None)
        if not animal_id:
            raise ValueError("animal must have a permanent animal_id")

        history = self.animal_repository.get_milking_frequency_history(animal_id)
        if history:
            record = self._matching_history(animal_id, op_date)
            if record is None:
                return None
            return str(record.milking_frequency).strip().upper()

        frequency = getattr(animal, "milking_frequency", None)
        return str(frequency).strip().upper() if frequency else None

    def get_expected_sessions(
        self, animal: Any, operational_date: date | datetime
    ) -> tuple[str, ...]:
        return self.sessions_for_frequency(
            self.get_frequency_for_date(animal, operational_date)
        )

    def get_schedule_snapshot(
        self, animal: Any, operational_date: date | datetime
    ) -> MilkingScheduleSnapshot:
        op_date = self._as_date(operational_date)
        animal_id = getattr(animal, "animal_id", None)
        if not animal_id:
            raise ValueError("animal must have a permanent animal_id")

        history = self.animal_repository.get_milking_frequency_history(animal_id)
        selected = self._matching_history(animal_id, op_date) if history else None

        if selected is not None:
            frequency = str(selected.milking_frequency).strip().upper()
            return MilkingScheduleSnapshot(
                animal_id=animal_id,
                operational_date=op_date,
                milking_frequency=frequency,
                expected_sessions=self.sessions_for_frequency(frequency),
                source="SCHEDULE_HISTORY",
                history_id=getattr(selected, "id", None),
                effective_from=getattr(selected, "effective_from", None),
                effective_to=getattr(selected, "effective_to", None),
                changed_by=getattr(selected, "changed_by", None),
                reason=getattr(selected, "reason", None),
            )

        if not history:
            frequency = getattr(animal, "milking_frequency", None)
            frequency = str(frequency).strip().upper() if frequency else None
            return MilkingScheduleSnapshot(
                animal_id=animal_id,
                operational_date=op_date,
                milking_frequency=frequency,
                expected_sessions=self.sessions_for_frequency(frequency),
                source="ANIMAL_CURRENT_FALLBACK",
            )

        return MilkingScheduleSnapshot(
            animal_id=animal_id,
            operational_date=op_date,
            milking_frequency=None,
            expected_sessions=(),
            source="NO_EFFECTIVE_SCHEDULE",
        )
