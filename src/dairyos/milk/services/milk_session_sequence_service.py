"""Milking-session sequencing (G3.1)."""

from __future__ import annotations

from datetime import date as date_type, datetime as datetime_type

from dairyos.milk.models.milking_session import MilkingSession
from dairyos.farm.herd.services.animal_milking_schedule_service import (
    AnimalMilkingScheduleService,
)

SESSION_ORDER: tuple[str, ...] = (
    MilkingSession.MORNING.value,
    MilkingSession.AFTERNOON.value,
    MilkingSession.EVENING.value,
)

CONDITIONAL_SESSIONS: frozenset[str] = frozenset(
    {MilkingSession.AFTERNOON.value}
)


class SequenceViolation(Exception):
    """Raised when a session is invalid or earlier sessions remain unsettled."""

    def __init__(
        self,
        *,
        operational_date,
        attempted_session: str,
        outstanding: list[str],
        reason: str = "OUT_OF_SEQUENCE",
    ):
        self.operational_date = operational_date
        self.attempted_session = str(attempted_session)
        self.outstanding = [str(item) for item in outstanding]
        self.reason = reason
        super().__init__(
            f"{self.attempted_session} cannot be recorded for "
            f"{self.operational_date}."
        )

    @property
    def blocking_session(self) -> str | None:
        return self.outstanding[0] if self.outstanding else None

    def as_operator_guidance(self) -> dict:
        if self.reason == "UNSCHEDULED_SESSION":
            return {
                "error": "MILKING_SESSION_NOT_IN_ANIMAL_SCHEDULE",
                "message": (
                    f"{self.attempted_session} is not an expected milking "
                    f"session for this animal on "
                    f"{_isoformat(self.operational_date)}."
                ),
                "operational_date": _isoformat(
                    self.operational_date
                ),
                "attempted_session": self.attempted_session,
                "outstanding_sessions": [],
                "next_session": None,
                "resolutions": [
                    {
                        "action": "USE_ANIMAL_SCHEDULE",
                        "description": (
                            "Use a session defined by the animal's effective "
                            "Animal Passport schedule."
                        ),
                        "endpoint": (
                            "GET /farm/animals/{animal_id}/passport"
                        ),
                    }
                ],
            }

        blocking = self.blocking_session

        return {
            "error": "MILKING_SESSION_OUT_OF_SEQUENCE",
            "message": (
                f"{self.attempted_session} cannot be recorded yet. "
                f"The {blocking} session for "
                f"{_isoformat(self.operational_date)} has not been "
                "recorded or declared."
            ),
            "operational_date": _isoformat(
                self.operational_date
            ),
            "attempted_session": self.attempted_session,
            "outstanding_sessions": list(self.outstanding),
            "next_session": blocking,
            "resolutions": [
                {
                    "action": "RECORD_SESSION",
                    "description": (
                        f"Enter the {blocking} milk figures."
                    ),
                    "endpoint": "POST /farm/milk",
                    "payload": {
                        "milking_session": blocking,
                        "production_date": _isoformat(
                            self.operational_date
                        ),
                    },
                },
                {
                    "action": "DECLARE_NOT_MILKED",
                    "description": (
                        f"Declare that the {blocking} milking did not "
                        "happen, with a reason."
                    ),
                    "endpoint": "POST /farm/milk/not-milked",
                    "payload": {
                        "milking_session": blocking,
                        "operational_date": _isoformat(
                            self.operational_date
                        ),
                        "reason": "<governed reason>",
                    },
                },
            ],
        }


class MilkSessionSequenceService:
    """Decide whether a milking session may be recorded for an animal/date."""

    def __init__(
        self,
        ledger_repository,
        *,
        schedule_service=None,
        milk_repository=None,
    ):
        self.ledger = ledger_repository
        self.schedule_service = schedule_service
        self.milk_repository = milk_repository

    def observed_sessions(self) -> list[str]:
        return [
            session
            for session in SESSION_ORDER
            if (
                session not in CONDITIONAL_SESSIONS
                or self.ledger.has_session_ever(session)
            )
        ]

    def _animal_settled_sessions(
        self,
        operational_date,
        animal=None,
    ) -> set[str]:
        """Return every settled occurrence for one animal/day.

        Animal MilkProduction is authoritative for recorded production.
        A farm-level session settlement is also authoritative because a
        whole-farm NOT_MILKED declaration settles that occurrence for every
        animal.
        """
        if animal is None or self.milk_repository is None:
            return self.ledger.settled_sessions_on(
                operational_date
            )

        animal_id = str(getattr(animal, "animal_id", ""))
        row = self.milk_repository.ledger_row_for_animal_day(
            animal_id,
            operational_date,
        )

        settled: set[str] = set()

        if (
            row is not None
            and str(
                getattr(row, "status", "") or ""
            ).upper() != "VOID"
        ):
            if getattr(row, "morning_yield", None) is not None:
                settled.add(MilkingSession.MORNING.value)

            if getattr(row, "afternoon_yield", None) is not None:
                settled.add(MilkingSession.AFTERNOON.value)

            if getattr(row, "evening_yield", None) is not None:
                settled.add(MilkingSession.EVENING.value)

        # A whole-farm session declaration settles the same occurrence
        # for every animal. This is essential for both shared MORNING
        # settlement and NOT_MILKED unblocking.
        settled.update(
            self.ledger.settled_sessions_on(
                operational_date
            )
        )

        return settled

    def settled_sessions_on(
        self,
        operational_date,
        *,
        animal=None,
    ) -> list[str]:
        """Return settled occurrences in the relevant authority."""
        if animal is None:
            settled = self.ledger.settled_sessions_on(
                operational_date
            )
        else:
            settled = self._animal_settled_sessions(
                operational_date,
                animal,
            )

        return [
            session
            for session in SESSION_ORDER
            if session in settled
        ]

    def outstanding_before(
        self,
        operational_date,
        milking_session: str,
        *,
        animal=None,
    ) -> list[str]:
        operational_date = _as_date(operational_date)
        milking_session = str(milking_session).upper()

        settled = self._animal_settled_sessions(
            operational_date,
            animal,
        )

        if self.schedule_service is not None and animal is not None:
            expected = tuple(
                self.schedule_service.get_expected_sessions(
                    animal,
                    operational_date,
                )
            )

            if expected:
                if milking_session not in expected:
                    return []

                position = expected.index(
                    milking_session
                )

                return [
                    session
                    for session in expected[:position]
                    if session not in settled
                ]

        if not self._is_sequenced(
            operational_date,
            milking_session,
        ):
            return []

        position = SESSION_ORDER.index(
            milking_session
        )

        return [
            session
            for session in self.observed_sessions()
            if SESSION_ORDER.index(session) < position
            and session not in settled
        ]

    def next_outstanding_session(
        self,
        operational_date,
    ) -> str | None:
        operational_date = _as_date(operational_date)
        settled = self.ledger.settled_sessions_on(
            operational_date
        )

        for session in self.observed_sessions():
            if session not in settled:
                return session

        return None

    def session_state(
        self,
        operational_date,
    ) -> dict:
        operational_date = _as_date(operational_date)
        records = self.ledger.get_by_date(
            operational_date
        )

        return {
            "operational_date": _isoformat(
                operational_date
            ),
            "observed_sessions": self.observed_sessions(),
            "next_session": self.next_outstanding_session(
                operational_date
            ),
            "settled_sessions": [
                {
                    "milking_session": str(
                        record.milking_session
                    ),
                    "status": str(record.status),
                    "reason": record.reason,
                    "session_record_id": (
                        record.session_record_id
                    ),
                }
                for record in records
            ],
        }

    def assert_can_record(
        self,
        operational_date,
        milking_session: str,
        *,
        animal=None,
    ) -> None:
        operational_date = _as_date(
            operational_date
        )
        milking_session = str(
            milking_session
        ).upper()

        if (
            self.schedule_service is not None
            and animal is not None
        ):
            expected = tuple(
                self.schedule_service.get_expected_sessions(
                    animal,
                    operational_date,
                )
            )

            if (
                expected
                and milking_session not in expected
            ):
                raise SequenceViolation(
                    operational_date=operational_date,
                    attempted_session=milking_session,
                    outstanding=[],
                    reason="UNSCHEDULED_SESSION",
                )

        outstanding = self.outstanding_before(
            operational_date,
            milking_session,
            animal=animal,
        )

        if outstanding:
            raise SequenceViolation(
                operational_date=operational_date,
                attempted_session=milking_session,
                outstanding=outstanding,
            )

    def _is_sequenced(
        self,
        operational_date,
        milking_session: str,
    ) -> bool:
        if milking_session not in SESSION_ORDER:
            return False

        if not self.ledger.has_any():
            return False

        earliest = self.ledger.earliest_date()

        return (
            earliest is None
            or operational_date >= earliest
        )


def _as_date(value):
    if value is None:
        return None

    if isinstance(value, datetime_type):
        return value.date()

    if isinstance(value, date_type):
        return value

    return date_type.fromisoformat(
        str(value)[:10]
    )


def _isoformat(value) -> str:
    value = _as_date(value)

    return (
        value.isoformat()
        if value is not None
        else ""
    )
