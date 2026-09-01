"""Canonical breeding-event classification for all DairyOS reproduction surfaces."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

CONFIRMED_RESULTS = {"pregnant", "confirmed", "positive", "yes"}
NEGATIVE_RESULTS = {"negative", "no"}

INSEMINATION_EVENTS = {"insemination", "service", "ai", "artificial_insemination"}

# A pregnancy_confirmed event is pregnancy-outcome evidence, not a separate
# pregnancy-check encounter. This distinction matters because the operator UI
# records both pregnancy_diagnosis and pregnancy_confirmed, and multiple
# positive observations must not inflate the number of conceptions.
PREGNANCY_CHECK_EVENTS = {
    "pregnancy_check",
    "pregnancy_diagnosis",
    "pregnancy",
    "pregnancy_negative",
}
CALVING_EVENTS = {"calving", "calved", "parturition"}
DRY_OFF_EVENTS = {"dry_off"}

EXPECTED_GESTATION_DAYS = 283
_EPOCH_MIN = datetime.min.replace(tzinfo=timezone.utc)


def normalize_event_type(value) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def normalize_result(value) -> str:
    return str(value or "").strip().lower()


def _event_type(record) -> str:
    return normalize_event_type(getattr(record, "event_type", None))


def _result(record) -> str:
    return normalize_result(getattr(record, "result", None))


def is_insemination(record) -> bool:
    return _event_type(record) in INSEMINATION_EVENTS


def is_pregnancy_check(record) -> bool:
    return _event_type(record) in PREGNANCY_CHECK_EVENTS


def is_negative_pregnancy_check(record) -> bool:
    if _event_type(record) == "pregnancy_negative":
        return True
    return is_pregnancy_check(record) and _result(record) in NEGATIVE_RESULTS


def is_confirmed_pregnancy(record) -> bool:
    if is_negative_pregnancy_check(record):
        return False
    return _event_type(record) == "pregnancy_confirmed" or (
        is_pregnancy_check(record) and _result(record) in CONFIRMED_RESULTS
    )


def is_calving(record) -> bool:
    return _event_type(record) in CALVING_EVENTS


def is_dry_off(record) -> bool:
    return _event_type(record) in DRY_OFF_EVENTS


def classify_animal_state(events) -> dict:
    """Per-animal current reproductive state via a last-event-wins walk."""
    ordered = sorted(events, key=lambda event: event.timestamp or _EPOCH_MIN)

    state = "UNKNOWN"
    last_ai = None
    pregnancy_result = None
    calving = None

    for event in ordered:
        if is_insemination(event):
            state = "INSEMINATED"
            last_ai = event.timestamp
        elif is_confirmed_pregnancy(event):
            state = "PREGNANT"
            pregnancy_result = event.result
        elif is_negative_pregnancy_check(event):
            state = "OPEN"
            pregnancy_result = event.result
        elif is_calving(event):
            state = "CALVED"
            calving = event.timestamp
        elif is_dry_off(event):
            state = "DRY_OFF"

    expected_calving = None
    if last_ai and state in {"INSEMINATED", "PREGNANT"}:
        expected_calving = (last_ai + timedelta(days=EXPECTED_GESTATION_DAYS)).isoformat()

    return {
        "state": state,
        "last_insemination": last_ai,
        "pregnancy_result": pregnancy_result,
        "expected_calving": expected_calving,
        "last_calving": calving,
    }
