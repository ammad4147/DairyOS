"""Entry-point-driven data-flow simulations.

These tests deliberately write through public farm entry points instead of
inserting domain rows directly. The simulations always consult the animal's
persisted Passport schedule before deciding which milking sessions are valid.
"""


def _bind_runtime_operational_state(container):
    container.runtime._operational_input_projection_bridge.state_service = (
        container.runtime._operational_state_service
    )


def _register_scheduled_animal(client, frequency):
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "COW",
            "breed": "Holstein",
            "lifecycle_status": "LACTATING",
            "is_currently_milking": True,
            "milking_frequency": frequency,
            "ear_tag": f"SIM-{frequency}-001",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["animal_id"]


def _passport_schedule(client, animal_id):
    response = client.get(f"/farm/animals/{animal_id}/passport")
    assert response.status_code == 200, response.text
    passport = response.json()
    frequency = passport["schedule"]["milking_frequency"]
    expected = passport["schedule"]["expected_sessions"]
    assert frequency in {"TWICE_DAILY", "THRICE_DAILY"}
    assert expected
    return frequency, expected


def test_milk_entry_flows_to_animal_passport_and_operations_dashboard(
    client,
    registered_animal,
):
    from dairyos.app import container

    _bind_runtime_operational_state(container)
    frequency, expected = _passport_schedule(client, registered_animal)
    assert frequency == "THRICE_DAILY"
    assert expected == ["MORNING", "AFTERNOON", "EVENING"]

    response = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "morning_yield": 8.0,
            "milking_session": "MORNING",
            "operator": "simulation",
        },
    )
    assert response.status_code == 200, response.text
    entry = response.json()
    assert entry["animal_id"] == registered_animal
    assert entry["morning_yield"] == 8.0
    assert entry["total_yield"] == 8.0
    assert entry.get("afternoon_yield") is None
    assert entry.get("evening_yield") is None

    passport = client.get(f"/farm/animals/{registered_animal}/passport")
    assert passport.status_code == 200, passport.text
    body = passport.json()
    assert any(
        row["animal_id"] == registered_animal
        and row["milking_session"] == "MORNING"
        and row["total_yield"] == 8.0
        for row in body["history"]["milk"]
    )
    assert body["production"]["lifetime"]["lifetime_milk_liters"] == 8.0

    operations = client.get("/operations/dashboard")
    assert operations.status_code == 200, operations.text
    assert operations.json()["milk_today"] == 8.0


def test_milk_entry_simulation_does_not_invent_unentered_sessions(
    client,
    registered_animal,
):
    from dairyos.app import container

    _bind_runtime_operational_state(container)
    _, expected = _passport_schedule(client, registered_animal)
    assert expected == ["MORNING", "AFTERNOON", "EVENING"]

    skipped = client.post(
        "/farm/milk/not-milked",
        json={
            "milking_session": "MORNING",
            "reason": "EQUIPMENT_FAILURE",
            "operator": "simulation",
        },
    )
    assert skipped.status_code == 200, skipped.text

    response = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "afternoon_yield": 0.0,
            "milking_session": "AFTERNOON",
            "operator": "simulation",
        },
    )
    assert response.status_code == 200, response.text
    entry = response.json()
    assert entry["afternoon_yield"] == 0.0
    assert entry["total_yield"] == 0.0
    assert entry.get("morning_yield") is None
    assert entry.get("evening_yield") is None


def test_thrice_daily_animal_requires_all_three_passport_sessions(client):
    from dairyos.app import container

    _bind_runtime_operational_state(container)
    animal_id = _register_scheduled_animal(client, "THRICE_DAILY")
    frequency, expected = _passport_schedule(client, animal_id)
    assert frequency == "THRICE_DAILY"
    assert expected == ["MORNING", "AFTERNOON", "EVENING"]

    morning = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "morning_yield": 8.0,
            "milking_session": "MORNING",
            "operator": "simulation",
        },
    )
    assert morning.status_code == 200, morning.text

    afternoon = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "afternoon_yield": 7.0,
            "milking_session": "AFTERNOON",
            "operator": "simulation",
        },
    )
    assert afternoon.status_code == 200, afternoon.text

    evening = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "evening_yield": 6.0,
            "milking_session": "EVENING",
            "operator": "simulation",
        },
    )
    assert evening.status_code == 200, evening.text

    passport = client.get(f"/farm/animals/{animal_id}/passport")
    assert passport.status_code == 200, passport.text
    data = passport.json()
    assert data["schedule"]["expected_sessions"] == expected
    rows = [row for row in data["history"]["milk"] if row["animal_id"] == animal_id]
    assert {row["milking_session"] for row in rows} >= set(expected)
    assert sum(row["total_yield"] for row in rows) == 21.0

    operations = client.get("/operations/dashboard")
    assert operations.status_code == 200, operations.text
    assert operations.json()["milk_today"] == 21.0


def test_twice_daily_animal_never_requires_afternoon(client):
    from dairyos.app import container

    _bind_runtime_operational_state(container)
    animal_id = _register_scheduled_animal(client, "TWICE_DAILY")
    frequency, expected = _passport_schedule(client, animal_id)
    assert frequency == "TWICE_DAILY"
    assert expected == ["MORNING", "EVENING"]

    morning = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "morning_yield": 8.0,
            "milking_session": "MORNING",
            "operator": "simulation",
        },
    )
    assert morning.status_code == 200, morning.text

    afternoon = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "afternoon_yield": 7.0,
            "milking_session": "AFTERNOON",
            "operator": "simulation",
        },
    )
    assert afternoon.status_code == 409, afternoon.text
    assert "AFTERNOON" in str(afternoon.json())

    evening = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "evening_yield": 6.0,
            "milking_session": "EVENING",
            "operator": "simulation",
        },
    )
    assert evening.status_code == 200, evening.text

    passport = client.get(f"/farm/animals/{animal_id}/passport")
    assert passport.status_code == 200, passport.text
    data = passport.json()
    assert data["schedule"]["milking_frequency"] == "TWICE_DAILY"
    assert data["schedule"]["expected_sessions"] == expected
    rows = [row for row in data["history"]["milk"] if row["animal_id"] == animal_id]
    assert {row["milking_session"] for row in rows} == {"MORNING", "EVENING"}
    assert sum(row["total_yield"] for row in rows) == 14.0
