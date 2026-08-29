"""Entry-point-driven data-flow simulations."""


def _bind_runtime_operational_state(container):
    container.runtime._operational_input_projection_bridge.state_service = (
        container.runtime._operational_state_service
    )


def test_milk_entry_flows_to_animal_passport_and_operations_dashboard(client, registered_animal):
    from dairyos.app import container
    _bind_runtime_operational_state(container)
    response = client.post("/farm/milk", json={
        "animal_id": registered_animal,
        "morning_yield": 8.0,
        "milking_session": "MORNING",
        "operator": "simulation",
    })
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


def test_milk_entry_simulation_does_not_invent_unentered_sessions(client, registered_animal):
    from dairyos.app import container
    _bind_runtime_operational_state(container)

    skipped = client.post("/farm/milk/not-milked", json={
        "milking_session": "MORNING",
        "reason": "EQUIPMENT_FAILURE",
        "operator": "simulation",
    })
    assert skipped.status_code == 200, skipped.text

    response = client.post("/farm/milk", json={
        "animal_id": registered_animal,
        "afternoon_yield": 0.0,
        "milking_session": "AFTERNOON",
        "operator": "simulation",
    })
    assert response.status_code == 200, response.text
    entry = response.json()
    assert entry["afternoon_yield"] == 0.0
    assert entry["total_yield"] == 0.0
    assert entry.get("morning_yield") is None
    assert entry.get("evening_yield") is None
