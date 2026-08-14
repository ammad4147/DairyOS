"""Same-session milk production drop detection (G3.4, AA-013 §7.5, D-UI-2/D-UI-3).

Compares one animal's yield for a session against the same animal/session's
most recent prior recorded day -- "session-to-session", never day-total, per
D-UI-2: a day-total comparison fires on every animal every morning (an
incomplete day always looks like a drop against a complete one) and would
discredit the feature within a week.

Excluded from detection, per §2.3 / §7.5: sessions with no entered yield
(NULL on every yield field), sessions declared NOT_MILKED, and rows with
`session_ledger=False` (pre-ledger history, where a stored 0.0 is ambiguous
and cannot be interpreted).

Deliberately a pure function over the same record shape `GET /farm/milk`
returns (the event-journal payload dicts `_list_by_type` produces in
`api/farm_data_entry.py`) rather than querying a separate SQL read path --
detection must never be able to disagree with what the operator sees on
screen, the same lesson G6.1's three-disagreeing-classifiers bug already
cost this project once.
"""

from datetime import date, datetime


def _record_date(record: dict) -> date | None:
    raw = record.get("production_date")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw)[:10]).date()
    except ValueError:
        return None


def _has_entered_yield(record: dict) -> bool:
    if record.get("total_yield") is not None:
        return True
    return any(
        record.get(field) is not None
        for field in ("morning_yield", "afternoon_yield", "evening_yield")
    )


def detect_drop(records: list[dict], *, animal_id: str, session: str, as_of_date: date) -> dict | None:
    """Compare `animal_id`'s `session` yield on `as_of_date` against that
    animal/session's most recent prior recorded day.

    Returns ``{"severity": "CRITICAL" | "HIGH" | None, "current": float,
    "previous": float, "percent": float, "previous_date": "YYYY-MM-DD"}``,
    or ``None`` when there's nothing eligible to compare against (first-ever
    session for this animal/session pair, or no persisted yield at all).

    Severity mapping is D-UI-3's red/amber onto the Operational Finding
    vocabulary (§4.3): red (decline > 20%) -> CRITICAL, amber (10-20%) ->
    HIGH, below 10% -> ``None`` (not a finding at all).
    """

    eligible = [
        r for r in records
        if str(r.get("animal_id")) == str(animal_id)
        and str(r.get("milking_session", "")).upper() == session.upper()
        and r.get("session_ledger") is True
        and str(r.get("status", "")).upper() != "NOT_MILKED"
        and _has_entered_yield(r)
    ]

    current_row = next((r for r in eligible if _record_date(r) == as_of_date), None)
    if current_row is None:
        return None

    prior_rows = sorted(
        (r for r in eligible if (_record_date(r) or as_of_date) < as_of_date),
        key=lambda r: _record_date(r) or as_of_date,
    )
    if not prior_rows:
        return None

    previous_row = prior_rows[-1]
    current = float(current_row.get("total_yield") or 0.0)
    previous = float(previous_row.get("total_yield") or 0.0)

    if previous <= 0:
        # A previous figure of zero (or nothing usable) has no meaningful
        # percentage decline -- avoid a divide-by-zero and a nonsensical
        # -100%-forever finding.
        return None

    percent = round(((current - previous) / previous) * 100, 1)

    if percent > -10:
        severity = None
    elif percent > -20:
        severity = "HIGH"
    else:
        severity = "CRITICAL"

    previous_date = _record_date(previous_row) or as_of_date

    return {
        "severity": severity,
        "current": current,
        "previous": previous,
        "percent": percent,
        "previous_date": previous_date.isoformat(),
    }
