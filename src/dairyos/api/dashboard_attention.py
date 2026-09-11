"""Authoritative, read-only attention lists used by the command dashboard.

The dashboard must surface current work, not lifetime event totals.  These
projections deliberately keep the append-only journal as the source of truth
while collapsing repeated vaccination records to the latest schedule for each
animal and vaccine.
"""

from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from typing import Any


def _as_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None


def _as_utc_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def vaccination_event_records(events: Iterable[Any], relational_records=None):
    """Yield non-void relational vaccinations plus legacy journal records.

    New records are deduplicated by their source event ID. The relational
    table is the authoritative source; the journal fallback preserves older
    installations until those records are migrated.
    """
    linked_event_ids = {
        getattr(row, "source_event_id", None)
        for row in (relational_records or [])
        if getattr(row, "source_event_id", None)
    }
    for event in events:
        if getattr(event, "name", None) != "OperationalInputReceived":
            continue
        payload = dict(getattr(event, "payload", {}) or {})
        if str(payload.get("input_type") or "").lower() != "vaccination":
            continue
        if str(payload.get("status") or "COMPLETED").upper() == "VOID":
            continue
        if getattr(event, "event_id", None) in linked_event_ids:
            continue
        yield event, payload

    for row in relational_records or []:
        if str(getattr(row, "status", "COMPLETED") or "COMPLETED").upper() == "VOID":
            continue
        yield (
            SimpleNamespace(
                event_id=getattr(row, "source_event_id", None),
                timestamp=getattr(row, "created_at", None),
            ),
            {
                "animal_id": row.animal_id,
                "vaccine": row.vaccine,
                "dose": row.dose,
                "administered_date": row.administered_date,
                "next_due_date": row.next_due_date,
                "schedule_status": row.schedule_status,
                "batch_number": row.batch_number,
                "veterinarian": row.veterinarian,
                "notes": row.notes,
                "operator": row.operator,
                "status": row.status,
            },
        )


def project_vaccination_schedule(
    events: Iterable[Any],
    operational_date: date,
    active_animal_ids: set[str] | None = None,
    relational_records=None,
) -> dict[str, Any]:
    """Project current vaccination schedules from append-only events.

    ``completed`` remains the lifetime record count for compatibility with
    existing reporting.  ``schedules`` and ``due`` are different: they use the
    latest persisted record per animal/vaccine, preventing an older due event
    from surviving after a newer vaccination was recorded.
    """
    records = list(
        vaccination_event_records(
            events,
            relational_records=relational_records,
        )
    )
    latest: dict[tuple[str, str], tuple[tuple[Any, ...], dict[str, Any]]] = {}

    for position, (event, payload) in enumerate(records):
        animal_id = str(payload.get("animal_id") or "").strip()
        vaccine = str(
            payload.get("vaccine") or payload.get("vaccination") or ""
        ).strip()
        if not animal_id or not vaccine:
            continue
        if active_animal_ids is not None and animal_id not in active_animal_ids:
            continue

        administered_date = _as_date(payload.get("administered_date"))
        event_time = _as_utc_datetime(
            getattr(event, "timestamp", None) or payload.get("timestamp")
        )
        rank = (
            event_time or datetime.min.replace(tzinfo=UTC),
            administered_date or date.min,
            position,
        )
        key = (animal_id, " ".join(vaccine.casefold().split()))
        previous = latest.get(key)
        if previous is None or rank > previous[0]:
            latest[key] = (rank, payload)

    schedules: list[dict[str, Any]] = []
    unscheduled: list[dict[str, Any]] = []
    for _, payload in latest.values():
        administered_date = _as_date(payload.get("administered_date"))
        next_due = _as_date(payload.get("next_due_date"))
        schedule_status = str(
            payload.get("schedule_status")
            or ("NEXT_DUE_DATE" if next_due is not None else "UNKNOWN_NEXT_DUE")
        ).upper()
        if next_due is None:
            unscheduled.append(
                {
                    "animal_id": str(payload.get("animal_id") or ""),
                    "vaccine": payload.get("vaccine") or payload.get("vaccination"),
                    "administered_date": (
                        administered_date.isoformat() if administered_date else ""
                    ),
                    "next_due_date": None,
                    "schedule_status": schedule_status,
                    "batch_number": payload.get("batch_number") or payload.get("batch"),
                    "veterinarian": payload.get("veterinarian") or payload.get("operator"),
                }
            )
            continue
        if next_due < operational_date:
            due_state = "OVERDUE"
        elif next_due == operational_date:
            due_state = "DUE_TODAY"
        else:
            due_state = "SCHEDULED"
        schedules.append(
            {
                "animal_id": str(payload.get("animal_id") or ""),
                "vaccine": payload.get("vaccine") or payload.get("vaccination"),
                "administered_date": (
                    administered_date.isoformat() if administered_date else ""
                ),
                "next_due_date": next_due.isoformat(),
                "schedule_status": schedule_status,
                "due_state": due_state,
                "batch_number": payload.get("batch_number") or payload.get("batch"),
                "veterinarian": payload.get("veterinarian") or payload.get("operator"),
            }
        )

    schedules.sort(
        key=lambda item: (
            item["next_due_date"],
            item["animal_id"],
            str(item.get("vaccine") or ""),
        )
    )
    unscheduled.sort(
        key=lambda item: (item["animal_id"], str(item.get("vaccine") or ""))
    )
    due = [
        item
        for item in schedules
        if item["next_due_date"] <= operational_date.isoformat()
    ]
    next_30 = operational_date + timedelta(days=30)
    return {
        "completed": len(records),
        "schedules": schedules,
        "unscheduled": unscheduled,
        "unscheduled_count": len(unscheduled),
        "due": due,
        "overdue": sum(item["due_state"] == "OVERDUE" for item in schedules),
        "due_next_30_days": sum(
            operational_date.isoformat()
            <= item["next_due_date"]
            <= next_30.isoformat()
            for item in schedules
        ),
    }
