"""Persistence for the herd-level milking session ledger."""

from __future__ import annotations

from datetime import date as date_type, datetime as datetime_type

from ..models.milking_session_record import MilkingSessionRecord


class MilkingSessionRecordRepository:
    """Read/write access to ``milking_session_records``.

    Supports the same in-memory fallback as the other DairyOS repositories so
    the sequencing service can be unit-tested without a database.
    """

    def __init__(self, session=None):
        self.session = session
        self.records: list[MilkingSessionRecord] = []

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def get_all(self):
        if self.session:
            return (
                self.session.query(MilkingSessionRecord)
                .order_by(
                    MilkingSessionRecord.operational_date.asc(),
                    MilkingSessionRecord.id.asc(),
                )
                .all()
            )

        return list(self.records)

    def get_by_date(self, operational_date: date_type):
        operational_date = _as_date(operational_date)

        if self.session:
            return (
                self.session.query(MilkingSessionRecord)
                .filter(
                    MilkingSessionRecord.operational_date == operational_date
                )
                .order_by(MilkingSessionRecord.id.asc())
                .all()
            )

        return [
            record
            for record in self.records
            if _as_date(record.operational_date) == operational_date
        ]

    def get_for(self, operational_date: date_type, milking_session: str):
        operational_date = _as_date(operational_date)
        milking_session = str(milking_session)

        if self.session:
            return (
                self.session.query(MilkingSessionRecord)
                .filter(
                    MilkingSessionRecord.operational_date == operational_date,
                    MilkingSessionRecord.milking_session == milking_session,
                )
                .first()
            )

        for record in self.records:
            if (
                _as_date(record.operational_date) == operational_date
                and str(record.milking_session) == milking_session
            ):
                return record

        return None

    def settled_sessions_on(self, operational_date: date_type) -> set[str]:
        """Sessions the farm has already made a statement about that day.

        Both RECORDED and NOT_MILKED count as settled -- the farm has said
        what happened either way.
        """

        return {
            str(record.milking_session)
            for record in self.get_by_date(operational_date)
        }

    def has_any(self) -> bool:
        if self.session:
            return (
                self.session.query(MilkingSessionRecord).first() is not None
            )

        return bool(self.records)

    def has_session_ever(self, milking_session: str) -> bool:
        """Whether the farm has ever settled this session at all.

        Used to decide which sessions a farm actually observes; see
        ``MilkSessionSequenceService``.
        """

        milking_session = str(milking_session)

        if self.session:
            return (
                self.session.query(MilkingSessionRecord)
                .filter(
                    MilkingSessionRecord.milking_session == milking_session
                )
                .first()
                is not None
            )

        return any(
            str(record.milking_session) == milking_session
            for record in self.records
        )

    def earliest_date(self):
        records = self.get_all()

        if not records:
            return None

        return min(_as_date(record.operational_date) for record in records)

    def count(self) -> int:
        if self.session:
            return self.session.query(MilkingSessionRecord).count()

        return len(self.records)

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    def next_session_record_id(self, operational_date: date_type) -> str:
        """Allocate the next ``MS-YYMMDD-NNN`` identifier for a day."""

        operational_date = _as_date(operational_date)
        prefix = f"MS-{operational_date:%y%m%d}-"

        existing = [
            str(record.session_record_id)
            for record in self.get_by_date(operational_date)
            if str(record.session_record_id or "").startswith(prefix)
        ]

        highest = 0
        for identifier in existing:
            suffix = identifier[len(prefix):]
            if suffix.isdigit():
                highest = max(highest, int(suffix))

        return f"{prefix}{highest + 1:03d}"

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def add(self, record: MilkingSessionRecord):
        if record.session_record_id is None:
            record.session_record_id = self.next_session_record_id(
                record.operational_date
            )

        if self.session:
            self.session.add(record)
            self.session.commit()
            self.session.refresh(record)
            return record

        self.records.append(record)
        return record

    def save(self, record: MilkingSessionRecord):
        """Compatibility persistence contract used by farm data entry."""

        return self.add(record)

    def settle(
        self,
        *,
        operational_date: date_type,
        milking_session: str,
        status: str,
        reason: str | None = None,
        notes: str | None = None,
        recorded_by: str | None = None,
    ):
        """Record what happened to a session, if not already stated.

        Idempotent by design: recording the second animal of a session must
        not attempt a second ledger row and trip the unique constraint.
        Returns the existing row unchanged when the session is already
        settled -- the first statement wins.
        """

        operational_date = _as_date(operational_date)

        existing = self.get_for(operational_date, milking_session)
        if existing is not None:
            return existing

        return self.add(
            MilkingSessionRecord(
                session_record_id=None,
                operational_date=operational_date,
                milking_session=str(milking_session),
                status=str(status),
                reason=reason,
                notes=notes,
                recorded_by=recorded_by,
            )
        )

    def delete_all(self) -> None:
        if self.session:
            self.session.query(MilkingSessionRecord).delete(
                synchronize_session=False
            )
            self.session.commit()
            return

        self.records.clear()


def _as_date(value):
    """Accept date, datetime or ISO string; return a plain date."""

    if value is None:
        return None

    if isinstance(value, datetime_type):
        return value.date()

    if isinstance(value, date_type):
        return value

    return date_type.fromisoformat(str(value)[:10])
