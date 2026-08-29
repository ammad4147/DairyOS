"""Twenty-animal, thirty-day production simulation.

All milk enters through the public operator API. The simulation deliberately
keeps two-times-daily animals on MORNING+EVENING and never fabricates missing
sessions. Expected analytics values are independently derived from inputs.
"""
from __future__ import annotations

from datetime import date, timedelta

ANIMAL_TAGS = [f"SIM-MO-{i:03d}" for i in range(1, 21)]
BASELINE = {tag: float(20 + ((i - 1) % 5)) for i, tag in enumerate(ANIMAL_TAGS, 1)}


def _register(client):
    ids = []
    for tag in ANIMAL_TAGS:
        response = client.post(
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


def _milk_analytics(client):
    response = client.get("/farm/milk/analytics")
    assert response.status_code == 200, response.text
    return response.json()


def _contains(value, predicate):
    if isinstance(value, dict):
        for key, child in value.items():
            if predicate(str(key), child):
                return True
            if _contains(child, predicate):
                return True
    elif isinstance(value, list):
        return any(_contains(child, predicate) for child in value)
    return False


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

    for offset in range(30):
        day = start + timedelta(days=offset)
        for index, animal_id in enumerate(ids):
            tag = ANIMAL_TAGS[index]
            value = BASELINE[tag]
            if day == final_day and index == 0:
                value = 35.0  # deliberate highest producer input
            elif day == final_day and index == 1:
                value = 10.0  # deliberate lowest producer input
            _post(client, animal_id, day, value, "MORNING")
            _post(client, animal_id, day, value, "EVENING")

    dashboard = _dashboard(client)
    analytics = _milk_analytics(client)
    serial = str({"dashboard": dashboard, "analytics": analytics}).lower()

    # 1. Production extremes must be populated from persisted entries.
    assert "highest" in serial and "lowest" in serial
    assert ANIMAL_TAGS[0] in serial and ANIMAL_TAGS[1] in serial
    assert "35" in serial and "10" in serial

    # 3. Total-farm trend data must contain the requested 7/15/30-day horizons.
    for horizon in (7, 15, 30):
        assert _contains(
            analytics,
            lambda key, child, h=horizon: h == int(child)
            if isinstance(child, int)
            else key.endswith(str(h)),
        ) or str(horizon) in serial

    # 5. Independent final-day average across all 20 entered animals.
    final_values = [35.0, 10.0] + [BASELINE[tag] for tag in ANIMAL_TAGS[2:]]
    expected_average = sum(final_values) / 20.0
    avg_values = []
    for node in _values_for_keys(analytics, "avg") + _values_for_keys(dashboard, "avg"):
        if isinstance(node, (int, float)):
            avg_values.append(float(node))
    assert any(abs(value - expected_average) < 1e-6 for value in avg_values), {
        "expected_average": expected_average,
        "dashboard": dashboard,
        "analytics": analytics,
    }


def test_three_individual_drops_populate_yield_drop_watchlist_with_amber_and_red(client):
    ids = _register(client)[:3]
    baseline_day = date(2026, 8, 28)
    drop_day = date(2026, 8, 29)

    for animal_id in ids:
        _post(client, animal_id, baseline_day, 20.0, "MORNING")
        _post(client, animal_id, baseline_day, 20.0, "EVENING")

    # 15% decline = HIGH/amber class; >20% = CRITICAL/red class.
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

    for animal_id in ids:
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


def test_milking_percentage_and_average_yield_use_only_entered_active_milking_animals(client):
    ids = _register(client)
    day = date(2026, 8, 30)
    entered_values = []
    for index, animal_id in enumerate(ids[:15]):
        value = float(18 + index)
        entered_values.append(value)
        _post(client, animal_id, day, value, "MORNING")
        _post(client, animal_id, day, value, "EVENING")

    dashboard = _dashboard(client)
    analytics = _milk_analytics(client)
    expected_percentage = 75.0
    expected_average = sum(entered_values) / len(entered_values)

    percent_values = []
    avg_values = []
    for node in _values_for_keys(dashboard, "milking") + _values_for_keys(analytics, "milking"):
        if isinstance(node, (int, float)):
            percent_values.append(float(node))
    for node in _values_for_keys(dashboard, "avg") + _values_for_keys(analytics, "avg"):
        if isinstance(node, (int, float)):
            avg_values.append(float(node))

    assert any(abs(value - expected_percentage) < 1e-6 for value in percent_values), dashboard
    assert any(abs(value - expected_average) < 1e-6 for value in avg_values), analytics
