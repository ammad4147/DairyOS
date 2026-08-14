"""Canonical breeding-event classification (Phase 1 fix, 2026-08-14).

Single source of truth for what a raw ``BreedingRecord.event_type`` means,
so the three live endpoints that all read the same records —
``api/farm_planning.py`` (per-animal current state), ``api/
reproduction_management.py`` (record-level counts, 365-day window) and
``api/dairy_kpi.py`` (record-level counts + interval KPIs, caller-specified
window) — classify identically instead of each keeping its own ad hoc
keyword list.

The real, actually-used vocabulary is the operator UI's breeding entry form
(``src/DairyOS.Web/src/App.tsx``'s ``entryConfigs.breeding`` field options):
``heat_detected``, ``insemination``, ``pregnancy_diagnosis``,
``pregnancy_confirmed``, ``pregnancy_negative``, ``dry_off``, ``calving``,
``abortion``, ``stillbirth``, ``postpartum_observation``. (Note:
``reference_data.py``'s ``GOVERNED["breeding_event_types"]`` is a separate,
unused, uppercase list that nothing actually reads for breeding entry — it
was reconciled to match this real vocabulary as part of the same fix, but
the operator UI does not currently source its dropdown from reference-data.
That's a smaller follow-up, not this fix.)

Before this fix, ``dairy_kpi.py`` never recognized ``pregnancy_diagnosis``
or ``pregnancy_confirmed`` as pregnancy-check events at all (it only matched
``pregnancy_check``/``pregnancy-check``/``pregnancy``), so its
``confirmed_pregnancies``/``conception_rate_percent`` silently undercounted
relative to ``reproduction_management.py`` for identical underlying data —
the concrete, provable divergence this closes.

``abortion``, ``stillbirth`` and ``postpartum_observation`` are real UI
options that none of the three endpoints classify today (they fall through
uncounted). That is a pre-existing gap, not a disagreement between the
three — left alone here to keep this fix scoped to reconciliation, not new
classification behavior; flagged in project memory for follow-up.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

CONFIRMED_RESULTS = {"pregnant", "confirmed", "positive", "yes"}
NEGATIVE_RESULTS = {"negative", "no"}

HEAT_DETECTION_EVENTS = {"heat_detection", "heat_detected", "heat", "oestrus", "estrus"}
INSEMINATION_EVENTS = {"insemination", "service", "ai", "artificial_insemination"}
PREGNANCY_CHECK_EVENTS = {"pregnancy_check", "pregnancy_diagnosis", "pregnancy", "pregnancy_negative"}
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


def is_heat_detection(record) -> bool:
    return _event_type(record) in HEAT_DETECTION_EVENTS


def is_insemination(record) -> bool:
    return _event_type(record) in INSEMINATION_EVENTS


def is_pregnancy_check(record) -> bool:
    return _event_type(record) in PREGNANCY_CHECK_EVENTS


def is_negative_pregnancy_check(record) -> bool:
    """A pregnancy check whose outcome is negative (open, not pregnant).

    ``pregnancy_negative`` as an event type is unambiguous on its own
    (that is the point of offering it as a distinct option) and does not
    require a matching ``result`` value, symmetric with how a bare
    ``pregnancy_confirmed`` event type is unambiguous in
    :func:`is_confirmed_pregnancy`.
    """
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
    """Per-animal current reproductive state via a last-event-wins walk.

    ``events`` is any iterable of objects exposing ``.event_type``,
    ``.result`` and ``.timestamp`` (a ``BreedingRecord`` or equivalent).
    Returns the fields ``api/farm_planning.py``'s ``/farm/animals/{id}/
    reproduction`` endpoint has always returned — this function replaces
    that endpoint's inline loop, it does not change its output shape.
    """
    ordered = sorted(events, key=lambda event: event.timestamp or _EPOCH_MIN)

    state = "UNKNOWN"
    last_heat = None
    last_ai = None
    pregnancy_result = None
    calving = None

    for event in ordered:
        if is_heat_detection(event):
            state = "HEAT_OBSERVED"
            last_heat = event.timestamp
        elif is_insemination(event):
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
        "last_heat": last_heat,
        "last_insemination": last_ai,
        "pregnancy_result": pregnancy_result,
        "expected_calving": expected_calving,
        "last_calving": calving,
    }
