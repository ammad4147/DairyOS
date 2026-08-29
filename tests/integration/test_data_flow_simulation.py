"""Public-entry-point milk flow simulations."""


def _runtime(client):
    from dairyos.app import container
    container.runtime._operational_input_projection_bridge.state_service = container.runtime._operational_state_service
    if getattr(container, "operational_command_center_service", None) is not None:
        container.operational_command_center_service.operational_state_service = container.runtime._operational_state_service
    return container


def _schedule(client, animal_id, as_of_date=None):
    response = client.get(f"/farm/animals/{animal_id}/passport", params={"as_of_date": as_of_date} if as_of_date else None)
    assert response.status_code == 200, response.text
    effective = response.json()["schedule"]["effective"]
    return effective["milking_frequency"], effective["expected_sessions"]


def _register(client, frequency):
    response = client.post("/farm/animals", json={
        "animal_type": "COW", "breed": "Holstein", "lifecycle_status": "LACTATING",
        "is_currently_milking": True, "milking_frequency": frequency,
        "ear_tag": f"SIM-{frequency}-001",
    })
    assert response.status_code == 200, response.text
    return response.json()["animal_id"]


def _milk_row(client, animal_id, production_date):
    body = client.get(f"/farm/animals/{animal_id}/passport", params={"as_of_date": production_date}).json()
    rows = [r for r in body["history"]["milk"] if r["animal_id"] == animal_id and str(r["production_date"]).startswith(production_date)]
    assert len(rows) == 1, rows
    return rows[0], body


def test_milk_entry_flows_to_animal_passport_and_operations_dashboard(client, registered_animal):
    container = _runtime(client)
    frequency, expected = _schedule(client, registered_animal)
    assert frequency == "THRICE_DAILY" and expected == ["MORNING", "AFTERNOON", "EVENING"]
    from dairyos.farm.settings.services.operational_date_authority import OperationalDateAuthority
    day = OperationalDateAuthority(repository_factory=container.repository_factory).current_date().isoformat()
    response = client.post("/farm/milk", json={"animal_id": registered_animal, "morning_yield": 8.0, "milking_session": "MORNING", "production_date": day, "operator": "simulation"})
    assert response.status_code == 200, response.text
    row, passport = _milk_row(client, registered_animal, day)
    assert row["morning_yield"] == 8.0 and row["afternoon_yield"] is None and row["evening_yield"] is None
    assert passport["production"]["lifetime"]["lifetime_milk_liters"] == 8.0
    operations = client.get("/operations/dashboard")
    assert operations.status_code == 200 and operations.json()["milk_today"] == 8.0


def test_thrice_daily_animal_requires_all_three_passport_sessions(client):
    _runtime(client)
    animal_id = _register(client, "THRICE_DAILY")
    assert _schedule(client, animal_id)[1] == ["MORNING", "AFTERNOON", "EVENING"]
    for session, field, value in (("MORNING", "morning_yield", 8.0), ("AFTERNOON", "afternoon_yield", 7.0), ("EVENING", "evening_yield", 6.0)):
        response = client.post("/farm/milk", json={"animal_id": animal_id, field: value, "milking_session": session, "operator": "simulation"})
        assert response.status_code == 200, response.text
    row, passport = _milk_row(client, animal_id, passport_day := passport_day_for(client, animal_id))
    assert (row["morning_yield"], row["afternoon_yield"], row["evening_yield"], row["total_yield"]) == (8.0, 7.0, 6.0, 21.0)
    assert passport["production"]["lifetime"]["lifetime_milk_liters"] == 21.0


def passport_day_for(client, animal_id):
    effective = client.get(f"/farm/animals/{animal_id}/passport").json()["schedule"]["effective"]
    return effective["operational_date"]


def test_twice_daily_animal_never_requires_afternoon(client):
    _runtime(client)
    animal_id = _register(client, "TWICE_DAILY")
    assert _schedule(client, animal_id)[1] == ["MORNING", "EVENING"]
    assert client.post("/farm/milk", json={"animal_id": animal_id, "morning_yield": 8.0, "milking_session": "MORNING", "operator": "simulation"}).status_code == 200
    blocked = client.post("/farm/milk", json={"animal_id": animal_id, "afternoon_yield": 7.0, "milking_session": "AFTERNOON", "operator": "simulation"})
    assert blocked.status_code == 409, blocked.text
    assert client.post("/farm/milk", json={"animal_id": animal_id, "evening_yield": 6.0, "milking_session": "EVENING", "operator": "simulation"}).status_code == 200
    row, _ = _milk_row(client, animal_id, passport_day_for(client, animal_id))
    assert row["morning_yield"] == 8.0 and row["afternoon_yield"] is None and row["evening_yield"] == 6.0 and row["total_yield"] == 14.0


def test_individual_passport_schedule_transition_changes_allowed_sessions(client):
    _runtime(client)
    animal_id = _register(client, "THRICE_DAILY")
    future = "2099-01-02"
    change = client.post(f"/farm/animals/{animal_id}/milking-frequency", json={"milking_frequency": "TWICE_DAILY", "changed_by": "simulation", "reason": "Simulation schedule transition", "effective_date": future})
    assert change.status_code == 200, change.text
    assert _schedule(client, animal_id, "2099-01-01")[1] == ["MORNING", "AFTERNOON", "EVENING"]
    assert _schedule(client, animal_id, future)[1] == ["MORNING", "EVENING"]
    assert client.post("/farm/milk", json={"animal_id": animal_id, "morning_yield": 9.0, "milking_session": "MORNING", "production_date": future, "operator": "simulation"}).status_code == 200
    blocked = client.post("/farm/milk", json={"animal_id": animal_id, "afternoon_yield": 7.0, "milking_session": "AFTERNOON", "production_date": future, "operator": "simulation"})
    assert blocked.status_code == 409, blocked.text
    assert client.post("/farm/milk", json={"animal_id": animal_id, "evening_yield": 8.0, "milking_session": "EVENING", "production_date": future, "operator": "simulation"}).status_code == 200
    row, _ = _milk_row(client, animal_id, future)
    assert row["morning_yield"] == 9.0 and row["afternoon_yield"] is None and row["evening_yield"] == 8.0 and row["total_yield"] == 17.0


def test_milk_entry_simulation_does_not_fabricate_an_unsettled_session(client, registered_animal):
    _runtime(client)
    assert _schedule(client, registered_animal)[1] == ["MORNING", "AFTERNOON", "EVENING"]
    blocked = client.post("/farm/milk", json={"animal_id": registered_animal, "afternoon_yield": 0.0, "milking_session": "AFTERNOON", "operator": "simulation"})
    assert blocked.status_code == 409, blocked.text
    skipped = client.post("/farm/milk/not-milked", json={"milking_session": "MORNING", "reason": "EQUIPMENT_FAILURE", "operator": "simulation"})
    assert skipped.status_code == 200, skipped.text
    response = client.post("/farm/milk", json={"animal_id": registered_animal, "afternoon_yield": 0.0, "milking_session": "AFTERNOON", "operator": "simulation"})
    assert response.status_code == 200, response.text
    assert response.json()["afternoon_yield"] == 0.0 and response.json()["morning_yield"] is None
