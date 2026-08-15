from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable

from dairyos.core.time_utils import utcnow


class AnimalMilkingScheduleService:
    """
    Converts an animal's governed milking-frequency instruction into
    expected operational milking sessions.

    Authority rules
    ---------------

    1. When an operational date is supplied, an effective-dated
       milking-frequency history record is authoritative for that date.

    2. History uses half-open date intervals:

           effective_from <= operational_date < effective_to

       A null effective_to means the record remains current.

    3. When no applicable history exists, the current
       ``animal.milking_frequency`` is used as a backwards-compatible
       fallback.

    4. The service never changes the animal's frequency.

    The service accepts an optional repository rather than opening a
    database connection itself. This preserves the application
    architecture: persistence remains outside the domain interpretation
    logic.
    """

    FREQUENCY_MAP = {
        "TWICE_DAILY": [
            "MORNING",
            "EVENING",
        ],
        "THRICE_DAILY": [
            "MORNING",
            "AFTERNOON",
            "EVENING",
        ],
    }

    def __init__(self, repository=None):
        self.repository = repository

    @staticmethod
    def _as_operational_date(
        operational_date: date | datetime | str | None,
    ) -> date | None:
        """
        Normalize a date-like value to a calendar date.

        ``None`` means: use current animal state rather than historical
        schedule resolution.
        """
        if operational_date is None:
            return None

        if isinstance(operational_date, datetime):
            return operational_date.date()

        if isinstance(operational_date, date):
            return operational_date

        if isinstance(operational_date, str):
            try:
                return date.fromisoformat(
                    operational_date
                )
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
        """
        Normalize history effective_from/effective_to values.

        History records are persisted as datetimes, while operational
        production authority is date-based.
        """
        if value is None:
            return None

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value).date()
            except ValueError:
                try:
                    return date.fromisoformat(value)
                except ValueError:
                    return None

        return None

    def _history_for_animal(
        self,
        animal,
    ) -> Iterable[Any]:
        """
        Obtain persisted schedule history when a repository is available.

        Returning an empty collection is deliberate for compatibility with
        memory-only/domain tests.
        """
        if self.repository is None:
            return []

        animal_id = getattr(
            animal,
            "animal_id",
            None,
        )

        if not animal_id:
            return []

        getter = getattr(
            self.repository,
            "get_milking_frequency_history",
            None,
        )

        if not callable(getter):
            return []

        history = getter(animal_id)

        return history or []

    def get_frequency_for_date(
        self,
        animal,
        operational_date: date | datetime | str | None = None,
        history: Iterable[Any] | None = None,
    ) -> str | None:
        """
        Resolve the milking frequency applicable on an operational date.

        If ``operational_date`` is omitted, the current Animal value is
        returned.

        ``history`` can be supplied explicitly for deterministic testing
        or callers that already loaded the schedule history.
        """
        normalized_date = self._as_operational_date(
            operational_date
        )

        current_frequency = getattr(
            animal,
            "milking_frequency",
            None,
        )

        if normalized_date is None:
            return current_frequency

        records = (
            list(history)
            if history is not None
            else list(
                self._history_for_animal(
                    animal
                )
            )
        )

        # Newest effective_from first is preferred, but sorting here also
        # makes the resolver robust against repository ordering changes.
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

            if effective_from is None:
                continue

            if normalized_date < effective_from:
                continue

            # Half-open interval:
            # [effective_from, effective_to)
            if (
                effective_to is not None
                and normalized_date >= effective_to
            ):
                continue

            frequency = getattr(
                record,
                "milking_frequency",
                None,
            )

            if frequency:
                return frequency

        return current_frequency

    def get_expected_sessions(
        self,
        animal,
        operational_date: date | datetime | str | None = None,
        history: Iterable[Any] | None = None,
    ):
        """
        Return expected milking sessions.

        Existing callers can continue using:

            get_expected_sessions(animal)

        Date-aware callers should use:

            get_expected_sessions(
                animal,
                operational_date=production_date,
            )
        """
        frequency = self.get_frequency_for_date(
            animal=animal,
            operational_date=operational_date,
            history=history,
        )

        if not frequency:
            return []

        return list(
            self.FREQUENCY_MAP.get(
                frequency,
                [],
            )
        )

    def get_schedule_snapshot(
        self,
        animal,
        operational_date: date | datetime | str | None = None,
        history: Iterable[Any] | None = None,
    ):
        """
        Return the operational schedule as read-model data.

        When an operational date is supplied, both frequency and expected
        sessions are resolved for that date.
        """
        normalized_date = self._as_operational_date(
            operational_date
        )

        frequency = self.get_frequency_for_date(
            animal=animal,
            operational_date=normalized_date,
            history=history,
        )

        return {
            "animal_id": animal.animal_id,
            "milking_frequency": frequency,
            "expected_sessions": self.get_expected_sessions(
                animal,
                operational_date=normalized_date,
                history=history,
            ),
            "operational_date": (
                normalized_date.isoformat()
                if normalized_date is not None
                else None
            ),
            "generated_at": utcnow(),
        }
