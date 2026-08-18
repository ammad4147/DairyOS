"""
Persistent append-only operational event journal.

Sprint-038
==========

Canonical event journal persistence boundary:

    Domain Event
        ↓
    PersistentEventJournal
        ↓
    JournalEntry
        ↓
    EventJournalModel
        ↓
    PostgreSQL

The journal:

- persists events;
- preserves event identity when supplied by the event;
- preserves event timestamps;
- reconstructs canonical Event instances for replay;
- supports controlled test/development clearing;
- provides journal inspection;
- provides persisted execution-sequence inspection.

The journal does NOT:

- publish events;
- invoke projections;
- execute business logic;
- rebuild operational state.
"""

from dairyos.data.database.models.event_journal_model import (
    EventJournalModel,
)

from dairyos.data.database.session import SessionLocal

from dairyos.domain.events import Event

from dairyos.runtime.journal_entry import JournalEntry


class PersistentEventJournal:
    """
    PostgreSQL-backed append-only operational event journal.

    Each operation owns a short-lived SQLAlchemy session.
    """

    def __init__(
        self,
        session_factory=SessionLocal,
    ):
        self._session_factory = session_factory

    def append(
        self,
        event,
    ):
        """
        Persist one domain event.
        """

        entry = JournalEntry.from_event(
            event
        )

        session = self._session_factory()

        try:
            model = EventJournalModel(
                event_id=entry.event_id,
                event_type=entry.event_type,
                timestamp=entry.timestamp,
                payload=entry.payload,
            )

            session.add(
                model
            )

            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    def clear(self):
        """
        Remove all journal entries.

        Intended for isolated tests and controlled development
        database resets.
        """

        session = self._session_factory()

        try:
            session.query(
                EventJournalModel
            ).delete(
                synchronize_session=False
            )

            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    def count(
        self,
    ):
        """
        Return the number of persisted journal entries.
        """

        session = self._session_factory()

        try:
            return (
                session.query(
                    EventJournalModel
                )
                .count()
            )

        finally:
            session.close()

    def latest(
        self,
        limit=10,
    ):
        """
        Return the latest journal records.

        Results are returned as dictionaries to preserve the
        journal inspection contract.
        """

        session = self._session_factory()

        try:
            rows = (
                session.query(
                    EventJournalModel
                )
                .order_by(
                    EventJournalModel.id.desc()
                )
                .limit(limit)
                .all()
            )

            return [
                {
                    "event_id": row.event_id,
                    "event_type": row.event_type,
                    "timestamp": row.timestamp,
                    "payload": row.payload,
                }
                for row in rows
            ]

        finally:
            session.close()

    def latest_execution_sequence(
        self,
    ) -> int:
        """
        Return the highest persisted EXE-#### execution number.

        Only OPERATIONAL_EXECUTION_CREATED events are considered.
        Malformed or legacy identifiers are ignored rather than
        blocking execution creation.
        """

        session = self._session_factory()

        try:
            rows = (
                session.query(
                    EventJournalModel
                )
                .filter(
                    EventJournalModel.event_type
                    == "OPERATIONAL_EXECUTION_CREATED"
                )
                .all()
            )

            highest = 0

            for row in rows:
                payload = dict(
                    row.payload or {}
                )

                execution_id = str(
                    payload.get(
                        "execution_id",
                        "",
                    )
                ).strip()

                if not execution_id.startswith("EXE-"):
                    continue

                sequence_text = execution_id[4:]

                if not sequence_text.isdigit():
                    continue

                sequence = int(
                    sequence_text
                )

                if sequence > highest:
                    highest = sequence

            return highest

        finally:
            session.close()

    def all_events(
        self,
    ):
        """
        Reconstruct all persisted events in append order.

        Replay reconstruction restores the canonical Event contract:

            name
            payload
            timestamp

        Persistence metadata remains owned by the journal boundary.
        """

        session = self._session_factory()

        try:
            rows = (
                session.query(
                    EventJournalModel
                )
                .order_by(
                    EventJournalModel.id.asc()
                )
                .all()
            )

            events = []

            for row in rows:
                payload = dict(
                    row.payload or {}
                )

                timestamp = ""

                if row.timestamp is not None:
                    timestamp = row.timestamp.isoformat()

                event = Event(
                    name=row.event_type,
                    payload=payload,
                    timestamp=timestamp,
                )

                events.append(
                    event
                )

            return events

        finally:
            session.close()
