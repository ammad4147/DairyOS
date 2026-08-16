"""Date-based individual milk-yield decline detection."""

from datetime import date
import pytest


def _row(
    animal_id="AN-TEST-001",
    production_date="2026-08-17",
    total_yield=10.0,
    morning_yield=10.0,
    afternoon_yield=None,
    evening_yield=0.0,
    session_ledger=True,
    status="MILKED",
):
    return {
        "animal_id": animal_id,
        "production_date": production_date,
        "total_yield": total_yield,
        "morning_yield": morning_yield,
        "afternoon_yield": afternoon_yield,
        "evening_yield": evening_yield,
        "session_ledger": session_ledger,
        "status": status,
    }


def _detect(records, as_of_date=date(2026, 8, 17)):
    from dairyos.farm.production.services.milk_drop_detection_service import detect_drop

    return detect_drop(
        records,
        animal_id="AN-TEST-001",
        session="EVENING",
        as_of_date=as_of_date,
        milking_frequency="TWICE_DAILY",
    )


def test_no_prior_date_means_nothing_to_compare():
    records = [_row(production_date="2026-08-17", total_yield=10.0, evening_yield=0.0)]
    result = _detect(records)
    assert result["status"] == "NO_COMPARABLE_PRIOR_DATE"


def test_complete_daily_total_is_compared_not_same_session():
    records = [
        _row(production_date="2026-08-16", morning_yield=12.0, evening_yield=8.0, total_yield=20.0),
        _row(production_date="2026-08-17", morning_yield=7.0, evening_yield=8.0, total_yield=15.0),
    ]
    result = _detect(records)
    assert result["status"] == "COMPLETE"
    assert result["current"] == 15.0
    assert result["previous"] == 20.0


def test_below_ten_percent_is_not_a_finding():
    records = [
        _row(production_date="2026-08-16", total_yield=20.0),
        _row(production_date="2026-08-17", total_yield=19.0),
    ]
    result = _detect(records)
    assert result["severity"] is None


def test_ten_to_twenty_percent_is_high_amber():
    records = [
        _row(production_date="2026-08-16", total_yield=20.0),
        _row(production_date="2026-08-17", total_yield=17.0),
    ]
    result = _detect(records)
    assert result["severity"] == "HIGH"


def test_exact_twenty_percent_is_high_amber():
    records = [
        _row(production_date="2026-08-16", total_yield=20.0),
        _row(production_date="2026-08-17", total_yield=16.0),
    ]
    result = _detect(records)
    assert result["severity"] == "HIGH"


def test_above_twenty_percent_is_critical_red():
    records = [
        _row(production_date="2026-08-16", total_yield=20.0),
        _row(production_date="2026-08-17", total_yield=10.0),
    ]
    result = _detect(records)
    assert result["severity"] == "CRITICAL"


def test_an_increase_is_never_a_finding():
    records = [
        _row(production_date="2026-08-16", total_yield=10.0),
        _row(production_date="2026-08-17", total_yield=16.0),
    ]
    result = _detect(records)
    assert result["severity"] is None


def test_not_milked_prior_date_is_not_a_comparable_date():
    records = [
        _row(production_date="2026-08-16", total_yield=0.0, status="NOT_MILKED", morning_yield=None, evening_yield=None),
        _row(production_date="2026-08-17", total_yield=10.0),
    ]
    result = _detect(records)
    assert result["status"] == "NO_COMPARABLE_PRIOR_DATE"


def test_null_yield_row_makes_the_date_incomplete():
    records = [
        _row(production_date="2026-08-16", total_yield=20.0),
        _row(production_date="2026-08-17", total_yield=None, morning_yield=10.0, evening_yield=None),
    ]
    result = _detect(records)
    assert result["status"] == "INCOMPLETE"


def test_pre_ledger_rows_are_excluded():
    records = [
        _row(production_date="2026-08-16", total_yield=99.0, session_ledger=False),
        _row(production_date="2026-08-17", total_yield=10.0),
    ]
    result = _detect(records)
    assert result["status"] == "NO_COMPARABLE_PRIOR_DATE"


def test_other_animals_are_never_compared():
    records = [
        _row(animal_id="AN-OTHER", production_date="2026-08-16", total_yield=999.0),
        _row(production_date="2026-08-17", total_yield=10.0),
    ]
    result = _detect(records)
    assert result["status"] == "NO_COMPARABLE_PRIOR_DATE"


def test_recording_complete_daily_milk_raises_a_real_drop_finding(client, registered_animal):
    frequency_response = client.post(
        f"/farm/animals/{registered_animal}/milking-frequency",
        json={
            "milking_frequency": "TWICE_DAILY",
            "changed_by": "test",
            "reason": "Configure twice-daily milk-drop detection test",
        },
    )
    assert frequency_response.status_code == 200, frequency_response.text
    assert frequency_response.json()["milking_frequency"] == "TWICE_DAILY"

    first_morning = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "milking_session": "MORNING",
            "morning_yield": 10.0,
            "production_date": "2026-08-16",
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
            "production_date": "2026-08-16",
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
            "production_date": "2026-08-17",
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
            "production_date": "2026-08-17",
            "operator": "Tester",
        },
    )
    assert second_evening.status_code == 200, second_evening.text

    findings = client.get("/farm/findings", params={"module": "MILK"}).json()["findings"]
    matching = [f for f in findings if f["subject_id"] == registered_animal and f["severity"] == "CRITICAL"]
    assert matching, "expected a MILK finding after a complete daily 60% drop"
    assert registered_animal in matching[0]["title"]

