"""Authoritative, read-only attention lists used by the command dashboard.

Vaccination scheduling is occurrence based.  Every relational vaccination row
represents one independently scheduled occurrence.  Administered occurrences
remain historical facts but are removed from current due/overdue attention.
Legacy journal-only installations remain readable as a compatibility fallback.
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
    """Yield relational vaccination occurrences plus legacy journal records.

    The relational table is authoritative for linked records.  Journal events
    whose source event IDs are already represented relationally are excluded.
    This preserves old journal-only installations without duplicating current
    relational records.
    """
    relational_records = list(relational_records or [])

    linked_event_ids = {
        getattr(row, "source_event_id", None)
        for row in relational_records
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

        # Administration endorses an existing relational occurrence.
        # It is an audit event, not another vaccination occurrence.
        if str(payload.get("event_action") or "").upper() in {
            "VACCINATION_ADMINISTERED",
            "ADMINISTERED",
            "VACCINATION_SCHEDULE_AMENDED",
            "SCHEDULE_AMENDED",
            "VACCINATION_SCHEDULE_VOIDED",
            "SCHEDULE_VOIDED",
        }:
            continue

        if getattr(event, "event_id", None) in linked_event_ids:
            continue

        yield event, payload

    for row in relational_records:
        if str(
            getattr(row, "status", "COMPLETED") or "COMPLETED"
        ).upper() == "VOID":
            continue

        yield (
            SimpleNamespace(
                event_id=getattr(row, "source_event_id", None),
                timestamp=getattr(row, "created_at", None),
            ),
            {
                "vaccination_occurrence_id": getattr(row, "id", None),
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
    """Project vaccination history and unresolved occurrence-level schedules."""

    relational_records = list(relational_records or [])

    records = list(
        vaccination_event_records(
            events,
            relational_records=relational_records,
        )
    )

    schedules: list[dict[str, Any]] = []
    unscheduled: list[dict[str, Any]] = []
    completed = 0

    for event, payload in records:
        animal_id = str(payload.get("animal_id") or "").strip()
        vaccine = str(
            payload.get("vaccine")
            or payload.get("vaccination")
            or ""
        ).strip()

        if not animal_id or not vaccine:
            continue

        if (
            active_animal_ids is not None
            and animal_id not in active_animal_ids
        ):
            continue

        administered_date = _as_date(
            payload.get("administered_date")
        )
        scheduled_date = _as_date(
            payload.get("next_due_date")
            or payload.get("scheduled_date")
        )
        schedule_status = str(
            payload.get("schedule_status")
            or (
                "NEXT_DUE_DATE"
                if scheduled_date is not None
                else "UNKNOWN_NEXT_DUE"
            )
        ).upper()

        if administered_date is not None:
            completed += 1
            continue

        if scheduled_date is None:
            unscheduled.append(
                {
                    "vaccination_occurrence_id": payload.get(
                        "vaccination_occurrence_id"
                    ),
                    "animal_id": animal_id,
                    "vaccine": vaccine,
                    "administered_date": "",
                    "next_due_date": None,
                    "schedule_status": schedule_status,
                    "batch_number": payload.get("batch_number")
                    or payload.get("batch"),
                    "veterinarian": payload.get("veterinarian")
                    or payload.get("operator"),
                }
            )
            continue

        if scheduled_date < operational_date:
            due_state = "OVERDUE"
        elif scheduled_date == operational_date:
            due_state = "DUE_TODAY"
        else:
            due_state = "SCHEDULED"

        schedules.append(
            {
                "vaccination_occurrence_id": payload.get(
                    "vaccination_occurrence_id"
                ),
                "animal_id": animal_id,
                "vaccine": vaccine,
                "administered_date": "",
                "next_due_date": scheduled_date.isoformat(),
                "schedule_status": schedule_status,
                "due_state": due_state,
                "batch_number": payload.get("batch_number")
                or payload.get("batch"),
                "veterinarian": payload.get("veterinarian")
                or payload.get("operator"),
            }
        )

    schedules.sort(
        key=lambda item: (
            item["next_due_date"],
            item["animal_id"],
            str(item.get("vaccine") or ""),
            int(item.get("vaccination_occurrence_id") or 0),
        )
    )

    unscheduled.sort(
        key=lambda item: (
            item["animal_id"],
            str(item.get("vaccine") or ""),
        )
    )

    due = [
        item
        for item in schedules
        if item["due_state"] in {"OVERDUE", "DUE_TODAY"}
    ]

    next_30 = operational_date + timedelta(days=30)

    return {
        "completed": completed,
        "schedules": schedules,
        "unscheduled": unscheduled,
        "unscheduled_count": len(unscheduled),
        "due": due,
        "overdue": sum(
            item["due_state"] == "OVERDUE"
            for item in schedules
        ),
        "due_next_30_days": sum(
            operational_date
            < date.fromisoformat(item["next_due_date"])
            <= next_30
            for item in schedules
        ),
    }
