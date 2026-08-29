"""Twenty-animal, thirty-day production simulation.

Fifteen animals are active lactating cows on TWICE_DAILY schedules; five are
active heifers and therefore must not be treated as milk-producing animals.
All milk enters through the public operator API. Expected analytics values are
independently derived from the supplied inputs.
"""
from __future__ import annotations

from datetime import date, timedelta

ANIMAL_TAGS = [f"SIM-MO-{i:03d}" for i in range(1, 21)]
MILKING_TAGS = ANIMAL_TAGS[:15]
BASELINE = {tag: float(20 + ((i - 1) % 5)) for i, tag in enumerate(ANIMAL_TAGS, 1)}


def _register(client):
    ids = []
    for index, tag in enumerate(ANIMAL_TAGS):
        lactating = index < 15
        response = client.post(
            "/farm/animals",
            json={
                "animal_type": "CATTLE",
                "ear_tag": tag,
                "breed": "HF",
                "sex": "FEMALE",
                "lifecycle_status": "LACTATING" if lactating else "HEIFER",
                "is_currently_milking": lactating,
                "milking_frequency": "TWICE_DAILY" if lactating else None,
            },
        )
        assert response.status_code == 200, response.text
        ids.append(response.json()["animal_id"])
    return ids


def _post(client, animal_id, day, litres, session):
    field = f"{session.lower()}_yield"
    response = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            field: litres,
            "milking_session": session,
            "production_date": day.isoformat(),
            "operator": "monthly-production-simulation",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _dashboard(client):
    response = client.get("/dashboard")
    assert response.status_code == 200, response.text
    return response.json()


def _milk_analytics(client, period_days=30):
    response = client.get("/farm/milk/analytics", params={"period_days": period_days})
    assert response.status_code == 200, response.text
    return response.json()


def _values_for_keys(value, needle):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            if needle.lower() in str(key).lower():
                found.append(child)
            found.extend(_values_for_keys(child, needle))
    elif isinstance(value, list):
        for child in value:
            found.extend(_values_for_keys(child, needle))
    return found


def test_twenty_animals_for_thirty_days_populate_extremes_trends_and_correct_kpis(client):
    ids = _register(client)
    start = date(2026, 8, 1)
    final_day = date(2026, 8, 30)
    milking_ids = ids[:15]

    for offset in range(30):
        day = start + timedelta(days=offset)
        for index, animal_id in enumerate(milking_ids):
            tag = MILKING_TAGS[index]
            value = BASELINE[tag]
            if day == final_day and index == 0:
                value = 35.0
            elif day == final_day and index == 1:
                value = 10.0
            _post(client, animal_id, day, value, "MORNING")
            _post(client, animal_id, day, value, "EVENING")

    dashboard = _dashboard(client)
    analytics = _milk_analytics(client, 30)

    extremes = analytics["production_extremes"]
    assert extremes["highest"]["animal_id"] == milking_ids[0]
    assert extremes["highest"]["total_litres"] == 70.0
    assert extremes["lowest"]["animal_id"] == milking_ids[1]
    assert extremes["lowest"]["total_litres"] == 20.0
    assert extremes["population_count"] == 15

    for horizon in (7, 15, 30):
        horizon_response = _milk_analytics(client, horizon)
        assert horizon_response["period_days"] == horizon
        assert horizon_response["trend"]["data_status"] == "LIVE_PERSISTED_DATA"
        assert horizon_response["trend"]["series"]

    final_values = [70.0, 20.0] + [2.0 * BASELINE[tag] for tag in MILKING_TAGS[2:]]
    expected_average_daily = sum(final_values) / 15.0
    avg_candidates = [
        float(node)
        for node in _values_for_keys(analytics, "avg") + _values_for_keys(dashboard, "avg")
        if isinstance(node, (int, float))
    ]
    assert any(abs(value - expected_average_daily) < 1e-6 for value in avg_candidates), {
        "expected_average_daily": expected_average_daily,
        "dashboard": dashboard,
        "analytics": analytics,
    }

    animals_payload = dashboard["animals"]
    assert animals_payload["total"] == 20
    assert animals_payload["milking"] == 15
    # Milking % is utilization of the 15-animal milking population, not
    # 15/20 total herd strength.
    assert dashboard["milk"]["milking_population_count"] == 15
    assert dashboard["milk"]["current_milking_count"] == 15
    assert dashboard["milk"]["milking_percentage"] == 100.0


def test_partial_daily_milking_is_measured_against_milking_population_not_total_herd(client):
    ids = _register(client)
    day = date(2026, 8, 30)
    for animal_id in ids[:12]:
        _post(client, animal_id, day, 20.0, "MORNING")
        _post(client, animal_id, day, 20.0, "EVENING")

    dashboard = _dashboard(client)
    assert dashboard["animals"]["total"] == 20
    assert dashboard["milk"]["milking_population_count"] == 15
    assert dashboard["milk"]["current_milking_count"] == 12
    assert dashboard["milk"]["milking_percentage"] == 80.0


def test_three_individual_drops_populate_yield_drop_watchlist_with_amber_and_red(client):
    ids = _register(client)[:3]
    baseline_day = date(2026, 8, 28)
    drop_day = date(2026, 8, 29)

    for animal_id in ids:
        _post(client, animal_id, baseline_day, 20.0, "MORNING")
        _post(client, animal_id, baseline_day, 20.0, "EVENING")

    for animal_id, value in ((ids[0], 17.0), (ids[1], 15.0), (ids[2], 10.0)):
        _post(client, animal_id, drop_day, value, "MORNING")
        _post(client, animal_id, drop_day, value, "EVENING")

    dashboard = _dashboard(client)
    serial = str(dashboard).lower()
    assert "yield" in serial and "drop" in serial
    assert all(animal_id in str(dashboard) for animal_id in ids)
    assert "amber" in serial or "high" in serial
    assert "red" in serial or "critical" in serial


def test_herd_drop_marks_production_date_and_drop_percentage_with_severity(client):
    ids = _register(client)
    baseline_day = date(2026, 8, 29)
    drop_day = date(2026, 8, 30)

    for animal_id in ids[:15]:
        _post(client, animal_id, baseline_day, 20.0, "MORNING")
        _post(client, animal_id, baseline_day, 20.0, "EVENING")
        value = 17.0 if animal_id != ids[0] else 12.0
        _post(client, animal_id, drop_day, value, "MORNING")
        _post(client, animal_id, drop_day, value, "EVENING")

    dashboard = _dashboard(client)
    serial = str(dashboard).lower()
    assert "production" in serial and "drop" in serial
    assert "%" in serial
    assert "amber" in serial or "red" in serial or "high" in serial or "critical" in serial
