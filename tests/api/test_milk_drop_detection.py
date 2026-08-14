"""Same-session milk production drop detection (G3.4, AA-013 §7.5, D-UI-2/D-UI-3).

Unit-tests the pure `detect_drop` function directly (severity thresholds,
same-session comparison, the §2.3 exclusions), then proves the wiring with
one integration test through the real `POST /farm/milk` endpoint.
"""

from datetime import date

from dairyos.farm.production.services.milk_drop_detection_service import detect_drop


def _row(**overrides):
    row = {
        "animal_id": "AN-TEST-001",
        "milking_session": "MORNING",
        "production_date": "2026-08-13",
        "total_yield": 20.0,
        "morning_yield": 20.0,
        "status": "RECORDED",
        "session_ledger": True,
    }
    row.update(overrides)
    return row


# ---------------------------------------------------------------------------
# Same-session comparison (D-UI-2)
# ---------------------------------------------------------------------------


def test_no_prior_session_means_nothing_to_compare():
    records = [_row(production_date="2026-08-14", total_yield=10.0)]
    result = detect_drop(records, animal_id="AN-TEST-001", session="MORNING", as_of_date=date(2026, 8, 14))
    assert result is None


def test_day_total_is_ignored_only_same_session_compared():
    records = [
        _row(production_date="2026-08-13", milking_session="EVENING", total_yield=1.0),
        _row(production_date="2026-08-13", milking_session="MORNING", total_yield=20.0),
        _row(production_date="2026-08-14", milking_session="MORNING", total_yield=19.0),
    ]
    result = detect_drop(records, animal_id="AN-TEST-001", session="MORNING", as_of_date=date(2026, 8, 14))
    assert result is not None
    assert result["previous"] == 20.0
    assert result["current"] == 19.0


# ---------------------------------------------------------------------------
# Severity thresholds (D-UI-3): red > 20%, amber 10-20%, none < 10%
# ---------------------------------------------------------------------------


def test_below_ten_percent_is_not_a_finding():
    records = [
        _row(production_date="2026-08-13", total_yield=20.0),
        _row(production_date="2026-08-14", total_yield=19.0),  # -5%
    ]
    result = detect_drop(records, animal_id="AN-TEST-001", session="MORNING", as_of_date=date(2026, 8, 14))
    assert result is not None
    assert result["severity"] is None


def test_ten_to_twenty_percent_is_high_amber():
    records = [
        _row(production_date="2026-08-13", total_yield=20.0),
        _row(production_date="2026-08-14", total_yield=17.0),  # -15%
    ]
    result = detect_drop(records, animal_id="AN-TEST-001", session="MORNING", as_of_date=date(2026, 8, 14))
    assert result["severity"] == "HIGH"


def test_above_twenty_percent_is_critical_red():
    records = [
        _row(production_date="2026-08-13", total_yield=20.0),
        _row(production_date="2026-08-14", total_yield=10.0),  # -50%
    ]
    result = detect_drop(records, animal_id="AN-TEST-001", session="MORNING", as_of_date=date(2026, 8, 14))
    assert result["severity"] == "CRITICAL"


def test_an_increase_is_never_a_finding():
    records = [
        _row(production_date="2026-08-13", total_yield=10.0),
        _row(production_date="2026-08-14", total_yield=16.0),  # +60%
    ]
    result = detect_drop(records, animal_id="AN-TEST-001", session="MORNING", as_of_date=date(2026, 8, 14))
    assert result["severity"] is None


# ---------------------------------------------------------------------------
# §2.3 exclusions
# ---------------------------------------------------------------------------


def test_not_milked_sessions_are_excluded():
    records = [
        # The most recent day before "today" was declared NOT_MILKED -- it
        # must never become "previous", even though it's the closest date.
        _row(production_date="2026-08-13", total_yield=0.0, status="NOT_MILKED"),
        _row(production_date="2026-08-12", total_yield=20.0),
        _row(production_date="2026-08-14", total_yield=10.0),
    ]
    result = detect_drop(records, animal_id="AN-TEST-001", session="MORNING", as_of_date=date(2026, 8, 14))
    assert result is not None
    assert result["previous"] == 20.0
    assert result["previous_date"] == "2026-08-12"


def test_null_yield_rows_are_excluded():
    records = [
        _row(production_date="2026-08-13", total_yield=None, morning_yield=None),
        _row(production_date="2026-08-12", total_yield=20.0),
        _row(production_date="2026-08-14", total_yield=10.0),
    ]
    result = detect_drop(records, animal_id="AN-TEST-001", session="MORNING", as_of_date=date(2026, 8, 14))
    assert result["previous"] == 20.0
    assert result["previous_date"] == "2026-08-12"


def test_pre_ledger_rows_are_excluded():
    records = [
        _row(production_date="2026-08-13", total_yield=99.0, session_ledger=False),
        _row(production_date="2026-08-12", total_yield=20.0, session_ledger=True),
        _row(production_date="2026-08-14", total_yield=10.0, session_ledger=True),
    ]
    result = detect_drop(records, animal_id="AN-TEST-001", session="MORNING", as_of_date=date(2026, 8, 14))
    assert result["previous"] == 20.0


def test_other_animals_and_other_sessions_never_compared():
    records = [
        _row(animal_id="AN-OTHER", production_date="2026-08-13", total_yield=999.0),
        _row(production_date="2026-08-13", milking_session="EVENING", total_yield=999.0),
        _row(production_date="2026-08-12", total_yield=20.0),
        _row(production_date="2026-08-14", total_yield=10.0),
    ]
    result = detect_drop(records, animal_id="AN-TEST-001", session="MORNING", as_of_date=date(2026, 8, 14))
    assert result["previous"] == 20.0


# ---------------------------------------------------------------------------
# Integration: the real POST /farm/milk endpoint raises a real finding
# ---------------------------------------------------------------------------


def test_recording_milk_raises_a_finding_on_a_real_drop(client, registered_animal):
    first = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "milking_session": "MORNING",
            "morning_yield": 20.0,
            "production_date": "2026-08-13",
            "operator": "Tester",
        },
    )
    assert first.status_code == 200, first.text

    second = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "milking_session": "MORNING",
            "morning_yield": 8.0,
            "production_date": "2026-08-14",
            "operator": "Tester",
        },
    )
    assert second.status_code == 200, second.text

    findings = client.get("/farm/findings", params={"module": "MILK"}).json()["findings"]
    matching = [f for f in findings if f["subject_id"] == registered_animal]
    assert matching, "expected a MILK finding for this animal after a 60% drop"
    assert matching[0]["severity"] == "CRITICAL"
    assert registered_animal in matching[0]["title"]
