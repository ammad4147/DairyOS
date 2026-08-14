"""Date-based individual milk-yield decline detection.

The governed comparison is one animal's complete daily total for a production
DATE against the immediately preceding DATE for that same animal. Session
entries are used only to establish completeness and interval compliance.
"""

from datetime import date


def _row(**overrides):
    row = {
        "animal_id": "AN-TEST-001",
        "production_date": "2026-08-14",
        "total_yield": 20.0,
        "morning_yield": 10.0,
        "afternoon_yield": None,
        "evening_yield": 10.0,
        "status": "RECORDED",
        "session_ledger": True,
    }
    row.update(overrides)
    return row


def _detect(records, as_of_date=date(2026, 8, 14)):
    from dairyos.farm.production.services.milk_drop_detection_service import detect_drop

    return detect_drop(
        records,
        animal_id="AN-TEST-001",
        session="EVENING",
        as_of_date=as_of_date,
        milking_frequency="TWICE_DAILY",
    )


def test_no_prior_date_means_nothing_to_compare():
    records = [_row(production_date="2026-08-14", total_yield=10.0, evening_yield=0.0)]
    result = _detect(records)
    assert result["status"] == "NO_COMPARABLE_PRIOR_DATE"
    assert result["severity"] is None


def test_complete_daily_total_is_compared_not_same_session():
    records = [
        _row(production_date="2026-08-13", morning_yield=12.0, evening_yield=8.0, total_yield=20.0),
        _row(production_date="2026-08-14", morning_yield=7.0, evening_yield=8.0, total_yield=15.0),
    ]
    result = _detect(records)
    assert result["status"] == "COMPLETE"
    assert result["previous"] == 20.0
    assert result["current"] == 15.0
    assert result["previous_date"] == "2026-08-13"
    assert result["current_date"] == "2026-08-14"


def test_below_ten_percent_is_not_a_finding():
    records = [
        _row(production_date="2026-08-13", total_yield=20.0),
        _row(production_date="2026-08-14", total_yield=19.0),
    ]
    result = _detect(records)
    assert result["severity"] is None


def test_ten_to_twenty_percent_is_high_amber():
    records = [
        _row(production_date="2026-08-13", total_yield=20.0),
        _row(production_date="2026-08-14", total_yield=17.0),
    ]
    result = _detect(records)
    assert result["severity"] == "HIGH"


def test_exact_twenty_percent_is_high_amber():
    records = [
        _row(production_date="2026-08-13", total_yield=20.0),
        _row(production_date="2026-08-14", total_yield=16.0),
    ]
    result = _detect(records)
    assert result["severity"] == "HIGH"


def test_above_twenty_percent_is_critical_red():
    records = [
        _row(production_date="2026-08-13", total_yield=20.0),
        _row(production_date="2026-08-14", total_yield=10.0),
    ]
    result = _detect(records)
    assert result["severity"] == "CRITICAL"


def test_an_increase_is_never_a_finding():
    records = [
        _row(production_date="2026-08-13", total_yield=10.0),
        _row(production_date="2026-08-14", total_yield=16.0),
    ]
    result = _detect(records)
    assert result["severity"] is None


def test_not_milked_prior_date_is_not_a_comparable_date():
    records = [
        _row(production_date="2026-08-13", total_yield=0.0, status="NOT_MILKED", morning_yield=None, evening_yield=None),
        _row(production_date="2026-08-14", total_yield=10.0),
    ]
    result = _detect(records)
    assert result["status"] == "NO_COMPARABLE_PRIOR_DATE"
    assert result["previous_date"] == "2026-08-13"


def test_null_yield_row_makes_the_date_incomplete():
    records = [
        _row(production_date="2026-08-13", total_yield=20.0),
        _row(production_date="2026-08-14", total_yield=None, morning_yield=10.0, evening_yield=None),
    ]
    result = _detect(records)
    assert result["status"] == "INCOMPLETE"
    assert result["missing_sessions"] == ["EVENING"]
    assert result["severity"] is None


def test_pre_ledger_rows_are_excluded():
    records = [
        _row(production_date="2026-08-13", total_yield=99.0, session_ledger=False),
        _row(production_date="2026-08-14", total_yield=10.0),
    ]
    result = _detect(records)
    assert result["status"] == "NO_COMPARABLE_PRIOR_DATE"


def test_other_animals_are_never_compared():
    records = [
        _row(animal_id="AN-OTHER", production_date="2026-08-13", total_yield=999.0),
        _row(production_date="2026-08-14", total_yield=10.0),
    ]
    result = _detect(records)
    assert result["status"] == "NO_COMPARABLE_PRIOR_DATE"


def test_recording_complete_daily_milk_raises_a_real_drop_finding(client, registered_animal):
    first_morning = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "milking_session": "MORNING",
            "morning_yield": 10.0,
            "production_date": "2026-08-13",
            "operator": "Tester",
        },
    )
    assert first_morning.status_code == 200, first_morning.text

    first_evening = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "milking_session": "EVENING",
            "evening_yield": 10.0,
            "production_date": "2026-08-13",
            "operator": "Tester",
        },
    )
    assert first_evening.status_code == 200, first_evening.text

    second_morning = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "milking_session": "MORNING",
            "morning_yield": 4.0,
            "production_date": "2026-08-14",
            "operator": "Tester",
        },
    )
    assert second_morning.status_code == 200, second_morning.text

    second_evening = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "milking_session": "EVENING",
            "evening_yield": 4.0,
            "production_date": "2026-08-14",
            "operator": "Tester",
        },
    )
    assert second_evening.status_code == 200, second_evening.text

    findings = client.get("/farm/findings", params={"module": "MILK"}).json()["findings"]
    matching = [f for f in findings if f["subject_id"] == registered_animal and f["severity"] == "CRITICAL"]
    assert matching, "expected a MILK finding after a complete daily 60% drop"
    assert registered_animal in matching[0]["title"]
