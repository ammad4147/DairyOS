"""Automatic post-calving return-to-milking reconciliation.

The operator-entered planned return date on a calving event is a governed
future herd-state transition, not informational text. This service applies
that transition idempotently against the farm operational date.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Any

from dairyos.data.models.animal import Animal
from dairyos.data.models.breeding_propagation_outbox import BreedingPropagationOutbox
from dairyos.data.database.models.event_journal_model import EventJournalModel
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)


_REASON = "POST_CALVING_PLANNED_RETURN"
_MILKING_FREQUENCIES = {"TWICE_DAILY", "THRICE_DAILY"}


def _as_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None


def _event_order(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    text = str(value or "").strip()
    if not text:
        return datetime.min
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return datetime.min


def persisted_breeding_payloads(repository_factory) -> list[dict]:
    """Read canonical database payloads, including undelivered breeding writes."""
    session = repository_factory.session
    payloads = [
        dict(row.payload or {})
        for row in session.query(EventJournalModel)
        .filter(EventJournalModel.event_type == "OperationalInputReceived").all()
        if str((row.payload or {}).get("input_type", "")).lower() == "breeding"
    ]
    payloads.extend(dict(row.payload or {}) for row in session.query(BreedingPropagationOutbox).all())
    return payloads


def _latest_calving_plans(repository_factory) -> dict[str, tuple[datetime, date]]:
    plans: dict[str, tuple[datetime, date]] = {}

    for payload in persisted_breeding_payloads(repository_factory):
        if str(payload.get("event_type") or "").strip().lower() not in {
            "calving",
            "calved",
            "parturition",
        }:
            continue

        animal_id = str(payload.get("animal_id") or "").strip()
        planned = _as_date(payload.get("planned_return_to_milking_date"))
        if not animal_id:
            continue

        order = _event_order(payload.get("timestamp"))
        current = plans.get(animal_id)
        if current is None or order >= current[0]:
            plans[animal_id] = (order, planned)

    return {key: value for key, value in plans.items() if value[1] is not None}


def _already_applied(repository, animal_id: str, planned: date) -> bool:
    for row in repository.get_milking_frequency_history(animal_id) or []:
        reason = str(getattr(row, "reason", "") or "").strip().upper()
        effective = _as_date(getattr(row, "effective_from", None))
        if reason == _REASON and effective == planned:
            return True
    return False


def _farm_frequency(repository, *, exclude_animal_id: str) -> str:
    frequencies = [
        str(getattr(animal, "milking_frequency", "") or "").strip().upper()
        for animal in repository.active_animals()
        if str(getattr(animal, "animal_id", "")) != exclude_animal_id
        and str(getattr(animal, "lifecycle_status", "") or "").upper() == "LACTATING"
        and bool(getattr(animal, "is_currently_milking", False))
        and str(getattr(animal, "milking_frequency", "") or "").strip().upper()
        in _MILKING_FREQUENCIES
    ]
    if frequencies:
        return Counter(frequencies).most_common(1)[0][0]
    return "THRICE_DAILY"


def reconcile_due_post_calving_returns(
    repository_factory,
    event_journal,
    *,
    as_of_date: date | None = None,
) -> list[str]:
    """Persist every due planned return exactly once and return animal IDs."""

    operational_date = as_of_date or OperationalDateAuthority(
        repository_factory=repository_factory
    ).current_date()

    repository = repository_factory.animal()
    session = repository_factory.session
    applied: list[str] = []

    try:
        for animal_id, (calved_at, planned) in _latest_calving_plans(repository_factory).items():
            if planned > operational_date:
                continue
            if calved_at.date() > operational_date or planned < calved_at.date():
                continue

            animal = (
                session.query(Animal)
                .filter(Animal.animal_id == animal_id)
                # Never wait indefinitely for a concurrent operator or
                # background transaction holding the mother row. Scheduler
                # callers fail fast and retry on the next reconciliation cycle.
                .with_for_update(nowait=True)
                .first()
            )
            if animal is None:
                continue
            # Check after taking the mother lock so concurrent readers cannot
            # both apply the same transition.
            if _already_applied(repository, animal_id, planned):
                continue
            if getattr(animal, "active", True) is False:
                continue
            if str(getattr(animal, "sex", "") or "").upper() != "FEMALE":
                continue

            # The planned post-calving transition applies only while the
            # mother remains in the Dry state created by that calving.
            if (
                str(getattr(animal, "lifecycle_status", "") or "").upper() != "DRY"
                or bool(getattr(animal, "is_currently_milking", False))
            ):
                continue

            history = repository.get_milking_frequency_history(animal_id) or []
            prior = [row for row in history
                     if (_as_date(row.effective_from) or date.max) <= planned
                     and row.milking_frequency in _MILKING_FREQUENCIES]
            frequency = (max(prior, key=lambda row: row.effective_from).milking_frequency
                         if prior else _farm_frequency(repository, exclude_animal_id=animal_id))

            animal.lifecycle_status = "LACTATING"
            animal.is_currently_milking = True
            repository.save(animal, commit=False)
            repository.set_milking_frequency(
                animal_id=animal_id,
                new_frequency=frequency,
                changed_by="DAIRYOS_SYSTEM",
                reason=_REASON,
                effective_date=planned,
                commit=False,
            )
            applied.append(animal_id)

        if applied:
            session.commit()
        return applied
    except Exception:
        session.rollback()
        raise
