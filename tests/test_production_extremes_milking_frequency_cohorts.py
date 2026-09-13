from datetime import date
from types import SimpleNamespace

from dairyos.api.milk_production_analytics import _production_extremes


class FakeTrendService:
    def __init__(self, rows):
        self.rows = rows

    def _daily_animal_snapshot(self, records, animal, histories, target_date):
        return self.rows.get((animal.animal_id, target_date.isoformat()))


def snapshot(animal_id, day, frequency, litres, *, complete=True):
    return {
        "animal_id": animal_id,
        "date": day,
        "frequency": frequency,
        "complete": complete,
        "missing_sessions": [] if complete else ["EVENING"],
        "total_litres": litres,
    }


def test_extremes_segregate_twice_and_thrice_and_exclude_incomplete_days():
    day = date(2026, 9, 13)
    animals = [SimpleNamespace(animal_id=value) for value in ("T1", "T2", "T3", "W1", "W2")]
    rows = {
        ("T1", day.isoformat()): snapshot("T1", day.isoformat(), "THRICE_DAILY", 31),
        ("T2", day.isoformat()): snapshot("T2", day.isoformat(), "THRICE_DAILY", 24),
        ("T3", day.isoformat()): snapshot("T3", day.isoformat(), "THRICE_DAILY", 5, complete=False),
        ("W1", day.isoformat()): snapshot("W1", day.isoformat(), "TWICE_DAILY", 21),
        ("W2", day.isoformat()): snapshot("W2", day.isoformat(), "TWICE_DAILY", 14),
    }

    result = _production_extremes(
        service=FakeTrendService(rows),
        records=[],
        animals=animals,
        histories={},
        target_date=day,
    )

    thrice = result["cohorts"]["THRICE_DAILY"]
    twice = result["cohorts"]["TWICE_DAILY"]

    assert thrice["population_count"] == 2
    assert twice["population_count"] == 2
    assert {row["animal_id"] for row in thrice["highest"] + thrice["lowest"]} == {"T1", "T2"}
    assert {row["animal_id"] for row in twice["highest"] + twice["lowest"]} == {"W1", "W2"}
    assert "T3" not in {row["animal_id"] for row in thrice["highest"] + thrice["lowest"]}
    assert result["highest"] == thrice["highest"]
    assert result["lowest"] == thrice["lowest"]


def test_each_frequency_uses_its_own_latest_completed_production_day():
    today = date(2026, 9, 13)
    yesterday = date(2026, 9, 12)
    animals = [SimpleNamespace(animal_id=value) for value in ("T1", "T2", "W1", "W2")]
    rows = {
        ("T1", today.isoformat()): snapshot("T1", today.isoformat(), "THRICE_DAILY", 20, complete=False),
        ("T2", today.isoformat()): snapshot("T2", today.isoformat(), "THRICE_DAILY", 18, complete=False),
        ("T1", yesterday.isoformat()): snapshot("T1", yesterday.isoformat(), "THRICE_DAILY", 30),
        ("T2", yesterday.isoformat()): snapshot("T2", yesterday.isoformat(), "THRICE_DAILY", 24),
        ("W1", today.isoformat()): snapshot("W1", today.isoformat(), "TWICE_DAILY", 22),
        ("W2", today.isoformat()): snapshot("W2", today.isoformat(), "TWICE_DAILY", 16),
    }

    result = _production_extremes(
        service=FakeTrendService(rows),
        records=[],
        animals=animals,
        histories={},
        target_date=today,
    )

    assert result["cohorts"]["THRICE_DAILY"]["production_date"] == yesterday.isoformat()
    assert result["cohorts"]["TWICE_DAILY"]["production_date"] == today.isoformat()
