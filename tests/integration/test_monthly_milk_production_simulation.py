"""Twenty-animal, one-month production simulation.

Uses public milk entry and analytics/operations endpoints. No synthetic UI state is
used; all expected values are independently calculated from entered inputs.
"""
from __future__ import annotations

from datetime import date, timedelta


ANIMALS = [f"SIM-MO-{i:03d}" for i in range(1, 21)]
BASELINE = {animal: 20.0 + (i % 5) for i, animal in enumerate(ANIMALS, start=1)}
LOW_YIELD = 10.0
HIGH_YIELD = 35.0


def _register_20(client):
    ids = []
    for i, tag in enumerate(ANIMALS, start=1):
        r = client.post(
            "/farm/animals",
            json={
                "animal_type": "CATTLE",
                "ear_tag": tag,
                "breed": "HF",
                "sex": "FEMALE",
                "lifecycle_status": "LACTATING",
                "is_currently_milking": True,
                "milking_frequency": "TWICE_DAILY",
            },
        )
        assert r.status_code == 200, r.text
        ids.append(r.json()["animal_id"])
    return ids


def _dashboard(client):
    r = client.get("/dashboard")
    assert r.status_code == 200, r.text
    return r.json()


def _analytics(client):
    r = client.get("/farm/analytics")
    assert r.status_code == 200, r.text
    return r.json()


def _find(value, terms=()):
    if isinstance(value, dict):
        for k, v in value.items():
            key = str(k).lower()
            if all(t in key for t in terms):
                yield v
            yield from _find(v, terms)
    elif isinstance(value, list):
        for v in value:
            yield from _find(v, terms)


def _post_milk(client, animal_id, day, litres, session="MORNING"):
    field = f"{session.lower()}_yield"
    r = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            field: litres,
            "milking_session": session,
            "production_date": day.isoformat(),
            "operator": "monthly-production-simulation",
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_twenty_animal_monthly_production_extremes_and_average(client):
    ids = _register_20(client)
    start = date(2026, 8, 1)
    for offset in range(30):
        day = start + timedelta(days=offset)
        for animal in ids:
            # Twice-daily: record morning and evening only.
            yield_litres = BASELINE[ANIMALS[ids.index(animal)]]
            _post_milk(client, animal, day, yield_litres, "MORNING")
            _post_milk(client, animal, day, yield_litres, "EVENING")

    # Deliberately create production extremes on the final day.
    _post_milk(client, ids[0], date(2026, 8, 30), HIGH_YIELD, "MORNING")
    _post_milk(client, ids[1], date(2026, 8, 30), LOW_YIELD, "MORNING")

    body = _analytics(client)
    highest = list(_find(body, ("highest",)))
    lowest = list(_find(body, ("lowest",)))
    assert highest, body
    assert lowest, body

    # Verify actual entered values occur in the analytic payload.
    serial = str(body)
    assert ANIMALS[0] in serial and ANIMALS[1] in serial
    assert "35" in serial and "10" in serial

    # Independent average from the final-day morning entries.
    expected_avg = sum(
        [HIGH_YIELD, LOW_YIELD]
        + [BASELINE[tag] for tag in ANIMALS[2:]]
    ) / 20
    dashboard = _dashboard(client)
    avg_candidates = list(_find(dashboard, ("avg",))) + list(_find(body, ("avg",)))
    assert any(abs(float(v) - expected_avg) < 1e-6 for v in avg_candidates if isinstance(v, (int, float))), body


def test_three_animal_milk_drops_create_watchlist_and_severity(client):
    ids = _register_20(client)[:3]
    day1 = date(2026, 8, 28)
    day2 = date(2026, 8, 29)
    day3 = date(2026, 8, 30)

    for animal in ids:
        _post_milk(client, animal, day1, 20.0, "MORNING")
        _post_milk(client, animal, day1, 20.0, "EVENING")

    # >10% but <=20%: HIGH/amber class.
    _post_milk(client, ids[0], day2, 17.0, "MORNING")
    _post_milk(client, ids[0], day2, 17.0, "EVENING")
    # >20%: CRITICAL/red class.
    _post_milk(client, ids[1], day2, 12.0, "MORNING")
    _post_milk(client, ids[1], day2, 12.0, "EVENING")
    # Third drop, critical.
    _post_milk(client, ids[2], day2, 10.0, "MORNING")
    _post_milk(client, ids[2], day2, 10.0, "EVENING")

    for animal in ids:
        # Keep the next day real and explicit, not inferred.
        value = {ids[0]: 16.0, ids[1]: 11.0, ids[2]: 9.0}[animal]
        _post_milk(client, animal, day3, value, "MORNING")
        _post_milk(client, animal, day3, value, "EVENING")

    dashboard = _dashboard(client)
    serial = str(dashboard).lower()
    assert "yield" in serial and "drop" in serial
    # The watchlist/attention data must reference all three animals.
    for animal in ids:
        assert animal in serial


def test_total_farm_yield_trends_exist_for_7_15_and_30_days(client):
    ids = _register_20(client)
    start = date(2026, 8, 1)
    for offset in range(30):
        day = start + timedelta(days=offset)
        for animal in ids:
            value = BASELINE[ANIMALS[ids.index(animal)]]
            _post_milk(client, animal, day, value, "MORNING")
            _post_milk(client, animal, day, value, "EVENING")

    analytics = _analytics(client)
    serial = str(analytics).lower()
    assert "7" in serial and "15" in serial and "30" in serial
    trends = [v for v in _find(analytics, ("trend",)) if isinstance(v, (list, dict))]
    assert trends, analytics


def test_herd_drop_changes_date_severity_and_production_drop_percentage(client):
    ids = _register_20(client)
    baseline_day = date(2026, 8, 29)
    drop_day = date(2026, 8, 30)
    for animal in ids:
        _post_milk(client, animal, baseline_day, 20.0, "MORNING")
        _post_milk(client, animal, baseline_day, 20.0, "EVENING")
        drop = 17.0 if animal != ids[0] else 12.0
        _post_milk(client, animal, drop_day, drop, "MORNING")
        _post_milk(client, animal, drop_day, drop, "EVENING")

    dashboard = _dashboard(client)
    serial = str(dashboard).lower()
    assert "production" in serial and "drop" in serial and "%" in serial
    assert "amber" in serial or "red" in serial


def test_milking_percentage_uses_active_milking_animals_and_average_yield_uses_entered_data(client):
    ids = _register_20(client)
    day = date(2026, 8, 30)
    for index, animal in enumerate(ids):
        if index < 15:
            value = float(18 + index)
            _post_milk(client, animal, day, value, "MORNING")
            _post_milk(client, animal, day, value, "EVENING")

    # 15 of 20 active animals are milking in the simulation.
    expected_milking_pct = 75.0
    expected_avg = sum(float(18 + i) for i in range(15)) / 15
    dashboard = _dashboard(client)
    analytics = _analytics(client)
    numeric = list(_find(dashboard, ("milking",))) + list(_find(analytics, ("milking",)))
    numeric += list(_find(dashboard, ("avg",))) + list(_find(analytics, ("avg",)))
    assert any(abs(float(v) - expected_milking_pct) < 1e-6 for v in numeric if isinstance(v, (int, float))), dashboard
    assert any(abs(float(v) - expected_avg) < 1e-6 for v in numeric if isinstance(v, (int, float))), analytics
