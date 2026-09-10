"""One PostgreSQL transaction for domain writes, journal, and delivery intent.

Legacy repository commits only end their ORM transaction: the connection's
outer transaction is owned here. No file or runtime projection runs until that
transaction has committed. The outbox references the existing canonical journal.
"""

import json
from copy import copy
from hashlib import sha256
from uuid import uuid4

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from dairyos.core.time_utils import utcnow
from dairyos.data.database.models.event_journal_model import EventJournalModel
from dairyos.data.models.operational_write import (
    OperationalProjectionOutbox,
    OperationalWrite,
)
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.domain.events.operational_input_received import OperationalInputReceived
from dairyos.runtime.persistent_event_journal import PersistentEventJournal


class RequestIdentityConflict(ValueError):
    """A retry identity was reused for different input."""


def _json(value):
    # Force serialization before committing any authoritative mutation.
    return json.loads(json.dumps(jsonable_encoder(value), allow_nan=False))


class TransactionInputGateway:
    def __init__(self, session, ingestion, request_id):
        self.session = session
        self.ingestion = ingestion
        self.request_id = request_id
        self.count = 0

    def record(self, input_type, payload, actor, **kwargs):
        event = self.ingestion.prepare(
            input_type=input_type,
            payload=_json(payload),
            source="farm_operator",
            actor=actor,
        )
        self.count += 1
        event.event_id = f"XSTORE-{self.request_id}-{self.count}"
        event.payload = _json(event.payload)
        row = PersistentEventJournal.append_in_session(self.session, event)
        self.session.add(
            OperationalProjectionOutbox(
                request_id=self.request_id, journal_id=row.id
            )
        )
        self.session.flush()
        return event


class OperationalWriteService:
    def __init__(self, engine, ingestion):
        self.engine = engine
        self.ingestion = ingestion

    def execute(self, *, request_id, request, mutation):
        request_id = request_id or str(uuid4())
        request_hash = sha256(
            json.dumps(_json(request), sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        # Serialize duplicates before invoking the mutation, including concurrent
        # submissions. PostgreSQL releases the advisory lock on commit/rollback.
        with self.engine.connect() as connection, connection.begin():
                connection.execute(
                    text("SELECT pg_advisory_xact_lock(:key)"),
                    {"key": int.from_bytes(sha256(request_id.encode()).digest()[:8], "big", signed=True)},
                )
                with Session(
                    bind=connection, join_transaction_mode="rollback_only",
                    expire_on_commit=False,
                ) as session:
                    session.info["operational_write_managed"] = True
                    receipt = session.get(OperationalWrite, request_id)
                    if receipt is not None:
                        if receipt.request_hash != request_hash:
                            raise RequestIdentityConflict(
                                "request_id was already accepted with different input"
                            )
                        response = dict(receipt.response)
                    else:
                        receipt = OperationalWrite(
                            request_id=request_id, request_hash=request_hash, response={}
                        )
                        session.add(receipt)
                        session.flush()
                        factory = RepositoryFactory(session)
                        gateway = TransactionInputGateway(session, self.ingestion, request_id)
                        response = _json(mutation(factory, gateway))
                        receipt.response = response
                        session.add(receipt)
                        session.flush()
                        if not connection.in_transaction():
                            raise RuntimeError("Authoritative write transaction was rolled back")
        # Delivery errors cannot turn a committed write into a rejected request.
        delivery = self.deliver_pending(request_id=request_id)
        return {**response, "request_id": request_id, "persistence_status": "ACCEPTED", **delivery}

    def deliver_pending(self, *, request_id=None):
        try:
            with Session(self.engine) as session, session.begin():
                # Serialize file delivery across workers, including different
                # requests. Reloading the JSON projection prevents stale instances
                # from overwriting another worker's delivered events.
                session.execute(text("SELECT pg_advisory_xact_lock(882341901)"))
                query = select(OperationalProjectionOutbox).where(
                    OperationalProjectionOutbox.status == "PENDING"
                ).order_by(OperationalProjectionOutbox.id)
                # Drain in append order even when a caller requests a later write.
                rows = session.scalars(query.with_for_update()).all()
                for row in rows:
                    journal = session.get(EventJournalModel, row.journal_id)
                    row.attempts += 1
                    try:
                        event = OperationalInputReceived(
                            input_type=journal.payload["input_type"],
                            payload=dict(journal.payload),
                            source=journal.payload["source"],
                            actor=journal.payload["actor"],
                            event_id=journal.event_id,
                            timestamp=journal.timestamp,
                        )
                        self.ingestion.deliver(event, durable=True)
                    except Exception as exc:  # noqa: BLE001 - delivery must remain retryable
                        row.last_error = f"{type(exc).__name__}: {exc}"[:1000]
                        break
                    row.status = "DELIVERED"
                    row.last_error = None
                    row.delivered_at = utcnow()
            return self.delivery_status(request_id=request_id)
        except Exception:  # noqa: BLE001 - preserve pending intent across delivery crashes
            # A crash or status-update failure leaves the durable intent pending.
            return {"projection_status": "DEGRADED"}

    def delivery_status(self, *, request_id=None):
        with Session(self.engine) as session:
            query = select(OperationalProjectionOutbox)
            if request_id is not None:
                query = query.where(OperationalProjectionOutbox.request_id == request_id)
            rows = session.scalars(query.order_by(OperationalProjectionOutbox.id)).all()
            return {
                "projection_status": "DEGRADED" if any(r.status != "DELIVERED" for r in rows) else "DELIVERED",
                "projection_events": [
                    {"outbox_id": r.id, "status": r.status, "attempts": r.attempts}
                    for r in rows
                ],
            }


def transaction_container(container, factory, gateway):
    """Request-local adapter; never replace the shared runtime's factory."""
    scoped = copy(container)
    scoped.repository_factory = factory
    scoped.input_gateway = gateway
    scoped._operational_write_active = True
    for name, accessor in (
        ("animal_repository", "animal"),
        ("treatment_repository", "treatment"),
        ("drug_reference_repository", "drug_reference"),
    ):
        if hasattr(container, name):
            setattr(scoped, name, getattr(factory, accessor)())
    if hasattr(container, "withdrawal_service"):
        from dairyos.operations.intelligence.services.withdrawal_service import (
            WithdrawalPeriod,
        )

        scoped.withdrawal_service = copy(container.withdrawal_service)
        scoped.withdrawal_service._periods = dict(container.withdrawal_service._periods)
        # Safety decisions use committed treatment authority even when its file
        # projection is pending. Never publish an uncommitted withdrawal period.
        for record in factory.treatment().get_all():
            if record.treated_at is not None and record.milk_withdrawal_until is not None:
                scoped.withdrawal_service.add_period(WithdrawalPeriod(
                    treatment_id=str(record.id), animal_id=record.animal_id,
                    start_time=record.treated_at, end_time=record.milk_withdrawal_until,
                ))
    return scoped
