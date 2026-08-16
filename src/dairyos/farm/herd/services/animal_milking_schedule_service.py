"""Authoritative animal-specific milking schedule interpretation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable

from dairyos.core.time_utils import utcnow
from dairyos.farm.production.models.non_milking_directive import (
    NonMilkingDirective,
)


FREQUENCY_MAP: dict[str, tuple[str, ...]] = {
    "TWICE_DAILY": ("MORNING", "EVENING"),
    "THRICE_DAILY": ("MORNING", "AFTERNOON", "EVENING"),
}


@dataclass(frozen=True)
class MilkingScheduleSnapshot:
    animal_id: str
    operational_date: date | None
    milking_frequency: str | None
    expected_sessions: tuple[str, ...]
    source: str
    history_id: int | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    changed_by: str | None = None
    reason: str | None = None
    non_milking_directive: str = NonMilkingDirective.NONE.value

    def __getitem__(self, key: str):
        if key == "operational_date":
            return (
                self.operational_date.isoformat()
                if self.operational_date is not None
                else None
            )

        if key == "expected_sessions":
            return list(self.expected_sessions)

        return getattr(self, key)


class AnimalMilkingScheduleService:
    """Single authority for interpreting an animal's milking schedule.

    Persisted authority is ``AnimalMilkingScheduleHistory``.

    Veterinary non-milking directives overlay the schedule:

    * NONE -> normal schedule applies.
    * TEMPORARY_NON_MILKING -> zero milk expected.
    * PERMANENT_NON_MILKING -> zero milk expected.
    * MILK_SEPARATELY -> milk is still expected, but the animal is outside
      the active normal milking-herd population. Downstream accounting can
      therefore classify its milk separately without treating it as a
      missed session.
    """

    FREQUENCY_MAP = FREQUENCY_MAP

    def __init__(self, repository=None):
        self.repository = repository

    @staticmethod
    def _as_operational_date(
        value: date | datetime | str | None,
    ) -> date | None:
        if value is None:
            return None

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError(
                    "operational_date must be YYYY-MM-DD"
                ) from exc

        raise TypeError(
            "operational_date must be date, datetime, "
            "YYYY-MM-DD string, or None"
        )

    @staticmethod
    def _history_date(value: Any) -> date | None:
        if value is None:
            return None

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        if isinstance(value, str):
            try:
                return datetime.fromisoformat(
                    value
                ).date()
            except ValueError:
                try:
                    return date.fromisoformat(value)
                except ValueError:
                    return None

        return None

    @staticmethod
    def _directive(animal) -> NonMilkingDirective:
        raw = getattr(
            animal,
            "non_milking_directive",
            NonMilkingDirective.NONE.value,
        )

        try:
            return NonMilkingDirective(str(raw))
        except ValueError:
            return NonMilkingDirective.NONE

    @classmethod
    def _directive_expects_milk(cls, animal) -> bool:
        return cls._directive(animal).expects_milk

    @classmethod
    def _directive_blocks_expected_milk(cls, animal) -> bool:
        directive = cls._directive(animal)

        return directive in {
            NonMilkingDirective.TEMPORARY_NON_MILKING,
            NonMilkingDirective.PERMANENT_NON_MILKING,
        }

    def _history_for_animal(self, animal) -> list[Any]:
        if self.repository is None:
            return []

        animal_id = getattr(
            animal,
            "animal_id",
            None,
        )

        getter = getattr(
            self.repository,
            "get_milking_frequency_history",
            None,
        )

        if not animal_id or not callable(getter):
            return []

        return list(
            getter(animal_id) or []
        )

    def _resolve_record(
        self,
        animal,
        operational_date,
        history=None,
    ):
        records = (
            list(history)
            if history is not None
            else self._history_for_animal(animal)
        )

        records.sort(
            key=lambda record: (
                self._history_date(
                    getattr(
                        record,
                        "effective_from",
                        None,
                    )
                )
                or date.min
            ),
            reverse=True,
        )

        for record in records:
            effective_from = self._history_date(
                getattr(
                    record,
                    "effective_from",
                    None,
                )
            )

            effective_to = self._history_date(
                getattr(
                    record,
                    "effective_to",
                    None,
                )
            )

            if (
                effective_from is None
                or operational_date < effective_from
            ):
                continue

            if (
                effective_to is not None
                and operational_date >= effective_to
            ):
                continue

            return record

        return None

    def get_frequency_for_date(
        self,
        animal,
        operational_date=None,
        history: Iterable[Any] | None = None,
    ) -> str | None:
        normalized = self._as_operational_date(
            operational_date
        )

        directive = self._directive(animal)

        # Temporary and permanent veterinary non-milking directives mean
        # there is deliberately no expected milk production.
        if self._directive_blocks_expected_milk(
            animal
        ):
            return None

        current = getattr(
            animal,
            "milking_frequency",
            None,
        )

        if normalized is None:
            return (
                str(current).strip().upper()
                if current
                else None
            )

        records = (
            list(history)
            if history is not None
            else self._history_for_animal(animal)
        )

        if not records:
            return (
                str(current).strip().upper()
                if current
                else None
            )

        record = self._resolve_record(
            animal,
            normalized,
            records,
        )

        if record is None:
            return None

        frequency = getattr(
            record,
            "milking_frequency",
            None,
        )

        return (
            str(frequency).strip().upper()
            if frequency
            else None
        )

    def get_expected_sessions(
        self,
        animal,
        operational_date=None,
        history: Iterable[Any] | None = None,
    ) -> list[str]:
        frequency = self.get_frequency_for_date(
            animal,
            operational_date,
            history,
        )

        return list(
            FREQUENCY_MAP.get(
                frequency,
                (),
            )
        )

    def get_schedule_snapshot(
        self,
        animal,
        operational_date=None,
        history: Iterable[Any] | None = None,
    ) -> MilkingScheduleSnapshot:
        normalized = self._as_operational_date(
            operational_date
        )

        directive = self._directive(animal)

        if self._directive_blocks_expected_milk(
            animal
        ):
            return MilkingScheduleSnapshot(
                animal_id=animal.animal_id,
                operational_date=normalized,
                milking_frequency=None,
                expected_sessions=(),
                source="VETERINARY_NON_MILKING",
                non_milking_directive=directive.value,
            )

        records = (
            list(history)
            if history is not None
            else self._history_for_animal(animal)
        )

        selected = (
            self._resolve_record(
                animal,
                normalized,
                records,
            )
            if normalized is not None and records
            else None
        )

        if selected is not None:
            frequency = (
                str(
                    getattr(
                        selected,
                        "milking_frequency",
                        "",
                    )
                ).strip().upper()
                or None
            )

            return MilkingScheduleSnapshot(
                animal_id=animal.animal_id,
                operational_date=normalized,
                milking_frequency=frequency,
                expected_sessions=FREQUENCY_MAP.get(
                    frequency,
                    (),
                ),
                source="SCHEDULE_HISTORY",
                history_id=getattr(
                    selected,
                    "id",
                    None,
                ),
                effective_from=getattr(
                    selected,
                    "effective_from",
                    None,
                ),
                effective_to=getattr(
                    selected,
                    "effective_to",
                    None,
                ),
                changed_by=getattr(
                    selected,
                    "changed_by",
                    None,
                ),
                reason=getattr(
                    selected,
                    "reason",
                    None,
                ),
                non_milking_directive=directive.value,
            )

        if not records:
            frequency = self.get_frequency_for_date(
                animal,
                normalized,
            )

            return MilkingScheduleSnapshot(
                animal_id=animal.animal_id,
                operational_date=normalized,
                milking_frequency=frequency,
                expected_sessions=FREQUENCY_MAP.get(
                    frequency,
                    (),
                ),
                source=(
                    "ANIMAL_CURRENT_FALLBACK"
                    if normalized is not None
                    else "ANIMAL_CURRENT"
                ),
                non_milking_directive=directive.value,
            )

        return MilkingScheduleSnapshot(
            animal_id=animal.animal_id,
            operational_date=normalized,
            milking_frequency=None,
            expected_sessions=(),
            source="NO_EFFECTIVE_SCHEDULE",
            non_milking_directive=directive.value,
        )
