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


def _latest_calving_plans(event_journal) -> dict[str, tuple[datetime, date]]:
    plans: dict[str, tuple[datetime, date]] = {}

    for event in event_journal.all_events():
        if getattr(event, "name", None) != "OperationalInputReceived":
            continue
        payload = dict(getattr(event, "payload", {}) or {})
        if str(payload.get("input_type") or "").strip().lower() != "breeding":
            continue
        if str(payload.get("event_type") or "").strip().lower() not in {
            "calving",
            "calved",
            "parturition",
        }:
            continue

        animal_id = str(payload.get("animal_id") or "").strip()
        planned = _as_date(payload.get("planned_return_to_milking_date"))
        if not animal_id or planned is None:
            continue

        order = _event_order(payload.get("timestamp") or getattr(event, "timestamp", None))
        current = plans.get(animal_id)
        if current is None or order >= current[0]:
            plans[animal_id] = (order, planned)

    return plans


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
        for animal_id, (_, planned) in _latest_calving_plans(event_journal).items():
            if planned > operational_date:
                continue
            if _already_applied(repository, animal_id, planned):
                continue

            animal = (
                session.query(Animal)
                .filter(Animal.animal_id == animal_id)
                .with_for_update()
                .first()
            )
            if animal is None:
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

            frequency = _farm_frequency(
                repository,
                exclude_animal_id=animal_id,
            )

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
