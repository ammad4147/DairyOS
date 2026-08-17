"""Milking-session sequencing (G3.1).

The farm records milk one session at a time, in order. If an operator can
enter an evening figure while the morning is still blank, the resulting gap is
indistinguishable from a genuinely empty session -- and every downstream
average, comparison and drop alert inherits that ambiguity.

This service refuses out-of-order entry and, crucially, always tells the
operator the two legitimate ways forward: record the outstanding session, or
declare it not milked.

Three restraints keep it from becoming an obstacle
==================================================

1. **An empty ledger blocks nothing.** A farm that was not running the ledger
   cannot be out of sequence with a period it was not recording.
2. **AFTERNOON is only sequenced once the farm records one.** A TWICE_DAILY
   farm milks morning and evening; treating the absent afternoon as
   outstanding would block every evening entry forever.
3. **Dates before the ledger began are not sequenced.** Backfilling history
   is not an out-of-sequence act.
"""

from __future__ import annotations

from datetime import date as date_type, datetime as datetime_type

from dairyos.milk.models.milking_session import MilkingSession
from dairyos.farm.herd.services.animal_milking_schedule_service import (
    AnimalMilkingScheduleService,
)


# The order the farm day runs in.
SESSION_ORDER: tuple[str, ...] = (
    MilkingSession.MORNING.value,
    MilkingSession.AFTERNOON.value,
    MilkingSession.EVENING.value,
)


# Sessions that are only sequenced once the farm has demonstrated it runs
# them. MORNING is never conditional -- nothing precedes it -- and EVENING is
# never skipped by a farm that runs any evening milking at all.
CONDITIONAL_SESSIONS: frozenset[str] = frozenset({
    MilkingSession.AFTERNOON.value,
})


class SequenceViolation(Exception):
    """Raised when a session is entered before an earlier one is settled."""

    def __init__(
        self,
        *,
        operational_date,
        attempted_session: str,
        outstanding: list[str],
    ):
        self.operational_date = operational_date
        self.attempted_session = str(attempted_session)
        self.outstanding = [str(item) for item in outstanding]

        super().__init__(
            f"{self.attempted_session} cannot be recorded for "
            f"{self.operational_date} while "
            f"{', '.join(self.outstanding)} "
            f"{'is' if len(self.outstanding) == 1 else 'are'} outstanding."
        )

    @property
    def blocking_session(self) -> str:
        """The earliest session the operator has to deal with first."""

        return self.outstanding[0]

    def as_operator_guidance(self) -> dict:
        """A refusal an operator can act on without asking anyone.

        Always names both routes. A farm that genuinely did not milk has to be
        able to say so, or the interlock becomes a reason to enter fiction.
        """

        blocking = self.blocking_session

        return {
            "error": "MILKING_SESSION_OUT_OF_SEQUENCE",
            "message": (
                f"{self.attempted_session} cannot be recorded yet. "
                f"The {blocking} session for "
                f"{_isoformat(self.operational_date)} has not been "
                f"recorded or declared."
            ),
            "operational_date": _isoformat(self.operational_date),
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
                        "production_date": _isoformat(self.operational_date),
                    },
                },
                {
                    "action": "DECLARE_NOT_MILKED",
                    "description": (
                        f"Declare that the {blocking} milking did not "
                        f"happen, with a reason."
                    ),
                    "endpoint": "POST /farm/milk/not-milked",
                    "payload": {
                        "milking_session": blocking,
                        "operational_date": _isoformat(self.operational_date),
                        "reason": "<governed reason>",
                    },
                },
            ],
        }


class MilkSessionSequenceService:
    """Decides whether a milking session may be recorded yet."""

    def __init__(
        self,
        ledger_repository,
        *,
        schedule_service=None,
    ):
        self.ledger = ledger_repository
        self.schedule_service = schedule_service

    # ------------------------------------------------------------------
    # Which sessions this farm actually runs
    # ------------------------------------------------------------------

    def observed_sessions(self) -> list[str]:
        """The sessions this farm's own history says it runs."""

        return [
            session
            for session in SESSION_ORDER
            if session not in CONDITIONAL_SESSIONS
            or self.ledger.has_session_ever(session)
        ]

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def outstanding_before(
        self,
        operational_date,
        milking_session: str,
        *,
        animal=None,
    ) -> list[str]:
        """Earlier unsettled sessions for the governed animal/date.

        When an animal and schedule service are supplied, the effective
        animal/date schedule is authoritative. The legacy farm-wide observed
        session model remains available for callers that do not provide an
        animal.
        """

        operational_date = _as_date(operational_date)
        milking_session = str(milking_session).upper()

        if not self._is_sequenced(operational_date, milking_session):
            return []

        settled = self.ledger.settled_sessions_on(operational_date)

        if self.schedule_service is not None and animal is not None:
            expected = tuple(
                self.schedule_service.get_expected_sessions(
                    animal,
                    operational_date,
                )
            )

            # An effective animal/date schedule is authoritative whenever
            # one exists. Historical dates without an effective schedule
            # retain the established ledger sequencing compatibility path.
            if expected:
                if milking_session not in expected:
                    return []

                position = expected.index(milking_session)

                return [
                    session
                    for session in expected[:position]
                    if session not in settled
                ]

        position = SESSION_ORDER.index(milking_session)

        return [
            session
            for session in self.observed_sessions()
            if SESSION_ORDER.index(session) < position
            and session not in settled
        ]

    def next_outstanding_session(self, operational_date) -> str | None:
        """The next session the farm owes a statement about, if any."""

        operational_date = _as_date(operational_date)
        settled = self.ledger.settled_sessions_on(operational_date)

        for session in self.observed_sessions():
            if session not in settled:
                return session

        return None

    def session_state(self, operational_date) -> dict:
        """Operator-facing view of one day's ledger."""

        operational_date = _as_date(operational_date)
        records = self.ledger.get_by_date(operational_date)

        return {
            "operational_date": _isoformat(operational_date),
            "observed_sessions": self.observed_sessions(),
            "next_session": self.next_outstanding_session(operational_date),
            "settled_sessions": [
                {
                    "milking_session": str(record.milking_session),
                    "status": str(record.status),
                    "reason": record.reason,
                    "session_record_id": record.session_record_id,
                }
                for record in records
            ],
        }

    # ------------------------------------------------------------------
    # Enforcement
    # ------------------------------------------------------------------

    def assert_can_record(
        self,
        operational_date,
        milking_session: str,
        *,
        animal=None,
    ) -> None:
        """Raise ``SequenceViolation`` if an earlier session is outstanding."""

        outstanding = self.outstanding_before(
            operational_date,
            milking_session,
            animal=animal,
        )

        if outstanding:
            raise SequenceViolation(
                operational_date=_as_date(operational_date),
                attempted_session=str(milking_session),
                outstanding=outstanding,
            )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _is_sequenced(self, operational_date, milking_session: str) -> bool:
        if milking_session not in SESSION_ORDER:
            return False

        # Restraint 1: nothing to be out of sequence with.
        if not self.ledger.has_any():
            return False

        # Restraint 3: history predating the ledger is a backfill.
        earliest = self.ledger.earliest_date()
        if earliest is not None and operational_date < earliest:
            return False

        return True


def _as_date(value):
    if value is None:
        return None

    if isinstance(value, datetime_type):
        return value.date()

    if isinstance(value, date_type):
        return value

    return date_type.fromisoformat(str(value)[:10])


def _isoformat(value) -> str:
    value = _as_date(value)

    return value.isoformat() if value is not None else ""
