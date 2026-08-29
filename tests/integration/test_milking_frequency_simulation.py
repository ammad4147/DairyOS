"""Animal-specific milking-frequency entry-point simulations."""


def _runtime():
    from dairyos.app import container
    container.runtime._operational_input_projection_bridge.state_service = container.runtime._operational_state_service
    if getattr(container, "operational_command_center_service", None) is not None:
        container.operational_command_center_service.operational_state_service = container.runtime._operational_state_service
    return container


def _effective(client, animal_id, as_of_date=None):
    params = {"as_of_date": as_of_date} if as_of_date else None
    response = client.get(f"/farm/animals/{animal_id}/passport", params=params)
    assert response.status_code == 200, response.text
    effective = response.json()["schedule"]["effective"]
    return effective


def _operational_date():
    from dairyos.app import container
    from dairyos.farm.settings.services.operational_date_authority import OperationalDateAuthority
    return OperationalDateAuthority(repository_factory=container.repository_factory).current_date().isoformat()


def _row(client, animal_id, day):
    assert day
    response = client.get(f"/farm/animals/{animal_id}/passport", params={"as_of_date": day})
    assert response.status_code == 200, response.text
    body = response.json()
    assert "history" in body and "milk" in body["history"], body
    rows = [r for r in body["history"]["milk"] if r["animal_id"] == animal_id and str(r["production_date"]).startswith(day)]
    assert len(rows) == 1, rows
    return rows[0], body


def test_thrice_daily_uses_passport_schedule_and_three_sessions(client, registered_animal):
    _runtime()
    schedule = _effective(client, registered_animal)
    assert schedule["milking_frequency"] == "THRICE_DAILY"
    assert schedule["expected_sessions"] == ["MORNING", "AFTERNOON", "EVENING"]
    day = _operational_date()
    for session, field, value in (("MORNING", "morning_yield", 8.0), ("AFTERNOON", "afternoon_yield", 7.0), ("EVENING", "evening_yield", 6.0)):
        response = client.post("/farm/milk", json={"animal_id": registered_animal, field: value, "milking_session": session, "production_date": day, "operator": "simulation"})
        assert response.status_code == 200, response.text
    row, passport = _row(client, registered_animal, day)
    assert (row["morning_yield"], row["afternoon_yield"], row["evening_yield"], row["total_yield"]) == (8.0, 7.0, 6.0, 21.0)
    assert passport["production"]["lifetime"]["lifetime_milk_liters"] == 21.0


def test_twice_daily_rejects_afternoon_and_accepts_evening(client):
    container = _runtime()
    created = client.post("/farm/animals", json={"animal_type": "COW", "breed": "HF", "lifecycle_status": "LACTATING", "is_currently_milking": True, "milking_frequency": "TWICE_DAILY", "ear_tag": "SIM-TWICE-FREQ-001"})
    assert created.status_code == 200, created.text
    animal_id = created.json()["animal_id"]
    schedule = _effective(client, animal_id)
    assert schedule["milking_frequency"] == "TWICE_DAILY"
    assert schedule["expected_sessions"] == ["MORNING", "EVENING"]
    day = _operational_date()
    assert client.post("/farm/milk", json={"animal_id": animal_id, "morning_yield": 9.0, "milking_session": "MORNING", "production_date": day, "operator": "simulation"}).status_code == 200
    blocked = client.post("/farm/milk", json={"animal_id": animal_id, "afternoon_yield": 5.0, "milking_session": "AFTERNOON", "production_date": day, "operator": "simulation"})
    assert blocked.status_code == 409, blocked.text
    assert client.post("/farm/milk", json={"animal_id": animal_id, "evening_yield": 8.0, "milking_session": "EVENING", "production_date": day, "operator": "simulation"}).status_code == 200
    row, passport = _row(client, animal_id, day)
    assert row["morning_yield"] == 9.0 and row["afternoon_yield"] is None and row["evening_yield"] == 8.0 and row["total_yield"] == 17.0
    assert passport["schedule"]["effective"]["expected_sessions"] == ["MORNING", "EVENING"]
