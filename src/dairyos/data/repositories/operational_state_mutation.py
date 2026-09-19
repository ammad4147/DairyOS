"""Concurrency-safe mutation boundary for the shared operational-state row."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from dairyos.core.time_utils import utcnow
from dairyos.data.database.models.operational_state_model import (
    OperationalStateModel,
)

Payload = dict[str, Any]
PayloadMutation = Callable[[Payload], Payload]


_ADVISORY_LOCK_NAMESPACE = 882344001


def _farm_lock_key(farm_id: str) -> int:
    """Return a stable signed 32-bit key for PostgreSQL advisory locking."""
    digest = hashlib.sha256(farm_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], byteorder="big", signed=True)


def _lock_farm_state(session: Session, farm_id: str) -> None:
    """Serialize one farm's state mutations, including first-row creation."""
    if session.bind is None or session.bind.dialect.name != "postgresql":
        return

    session.execute(
        text("SELECT pg_advisory_xact_lock(:namespace, :farm_key)"),
        {
            "namespace": _ADVISORY_LOCK_NAMESPACE,
            "farm_key": _farm_lock_key(farm_id),
        },
    )


def mutate_operational_state(
    session: Session,
    *,
    farm_id: str,
    operational_date: str | date,
    mutation: PayloadMutation,
    created_at: datetime | None = None,
) -> OperationalStateModel:
    """Apply one atomic read-modify-write to a farm's shared JSON envelope.

    The transaction-scoped advisory lock protects the no-row case. The row
    lock documents and enforces the same invariant once the row exists. The
    caller owns commit or rollback so this operation can participate in a
    larger business transaction.
    """
    normalized_farm_id = farm_id.strip()
    if not normalized_farm_id:
        raise ValueError("farm_id is required")

    _lock_farm_state(session, normalized_farm_id)

    model = (
        session.query(OperationalStateModel)
        .filter(OperationalStateModel.farm_id == normalized_farm_id)
        .with_for_update()
        .one_or_none()
    )

    if model is None:
        model = OperationalStateModel(
            farm_id=normalized_farm_id,
            operational_date=operational_date,
            state_payload={},
            created_at=created_at or utcnow(),
        )
        session.add(model)
        session.flush()

    current_payload = dict(model.state_payload or {})
    next_payload = mutation(current_payload)
    if not isinstance(next_payload, dict):
        raise TypeError("operational-state mutation must return a dict payload")

    model.operational_date = operational_date
    model.state_payload = next_payload
    session.flush()
    return model
