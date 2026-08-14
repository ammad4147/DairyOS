from datetime import date

import pytest

from dairyos.farm.production.services.milk_daily_semantics import (
    expected_sessions,
    is_complete,
    missing_sessions,
)
from dairyos.farm.production.services.milk_drop_detection_service import detect_drop


DAY = date(2026, 8, 15)
PRIOR = date(2026, 8, 14)


def row(day, *, morning=None, afternoon=None, evening=None, total=None):
    return {
        "animal_id": "AN-1",
        "production_date": day,
        "session_ledger": True,
        "status": "RECORDED",
        "morning_yield": morning,
        "afternoon_yield": afternoon,
        "evening_yield": evening,
        "total_yield": total,
    }


def test_twice_daily_requires_morning_and_evening():
    assert expected_sessions("TWICE_DAILY") == ("MORNING", "EVENING")
    assert missing_sessions(row(DAY, morning=5.0), "TWICE_DAILY") == ("EVENING",)
    assert is_complete(row(DAY, morning=5.0, evening=5.0), "TWICE_DAILY")


def test_thrice_daily_requires_all_three_sessions():
    assert missing_sessions(
        row(DAY, morning=4.0, evening=4.0),
        "THRICE_DAILY",
    ) == ("AFTERNOON",)
    assert is_complete(
        row(DAY, morning=4.0, afternoon=4.0, evening=4.0),
        "THRICE_DAILY",
    )


def test_null_is_not_zero_for_completeness():
    assert not is_complete(
        row(DAY, morning=0.0, evening=None),
        "TWICE_DAILY",
    )


@pytest.mark.parametrize(
    "current,previous,expected_severity",
    [
        (90.0, 100.0, "HIGH"),
        (80.0, 100.0, "HIGH"),
        (79.9, 100.0, "CRITICAL"),
        (95.0, 100.0, None),
        (110.0, 100.0, None),
    ],
)
def test_complete_daily_drop_thresholds(current, previous, expected_severity):
    records = [
        row(PRIOR, morning=50.0, evening=50.0, total=previous),
        row(DAY, morning=current / 2, evening=current / 2, total=current),
    ]
    result = detect_drop(
        records,
        animal_id="AN-1",
        as_of_date=DAY,
        milking_frequency="TWICE_DAILY",
    )
    assert result["status"] == "COMPLETE"
    assert result["severity"] == expected_severity


def test_drop_uses_complete_daily_total_not_same_session():
    records = [
        row(PRIOR, morning=60.0, evening=40.0, total=100.0),
        row(DAY, morning=30.0, evening=50.0, total=80.0),
    ]
    result = detect_drop(
        records,
        animal_id="AN-1",
        session="EVENING",
        as_of_date=DAY,
        milking_frequency="TWICE_DAILY",
    )
    assert result["previous_date"] == "2026-08-14"
    assert result["current_date"] == "2026-08-15"
    assert result["previous"] == 100.0
    assert result["current"] == 80.0
    assert result["severity"] == "HIGH"


def test_incomplete_current_date_has_formal_no_comparison_state():
    records = [
        row(PRIOR, morning=50.0, evening=50.0, total=100.0),
        row(DAY, morning=80.0),
    ]
    result = detect_drop(
        records,
        animal_id="AN-1",
        as_of_date=DAY,
        milking_frequency="TWICE_DAILY",
    )
    assert result["status"] == "INCOMPLETE"
    assert result["severity"] is None
    assert result["missing_sessions"] == ["EVENING"]
