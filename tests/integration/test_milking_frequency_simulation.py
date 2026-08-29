"""Entry-point simulations for animal-specific milking frequency."""


def _bind_runtime_operational_state(container):
    container.runtime._operational_input_projection_bridge.state_service = (
        container.runtime._operational_state_service
    )


def _passport_schedule(client, animal_id):
    response = client.get(f"/farm/animals/{animal_id}/passport")
    assert response.status_code == 200, response.text
    body = response.json()
    schedule = body.get("schedule") or {}
    return body, schedule


def test_thrice_daily_uses_passport_schedule_and_three_sessions(
    client,
    registered_animal,
):
    from dairyos.app import container

    _bind_runtime_operational_state(container)
    body, schedule = _passport_schedule(client, registered_animal)

    assert schedule["milking_frequency"] == "THRICE_DAILY", body
    assert schedule["expected_sessions"] == [
        "MORNING",
        "AFTERNOON",
        "EVENING",
    ], body

    for session, field, value in (
        ("MORNING", "morning_yield", 8.0),
        ("AFTERNOON", "afternoon_yield", 7.0),
        ("EVENING", "evening_yield", 6.0),
    ):
        response = client.post(
            "/farm/milk",
            json={
                "animal_id": registered_animal,
                field: value,
                "milking_session": session,
                "operator": "simulation",
            },
        )
        assert response.status_code == 200, response.text

    passport = client.get(f"/farm/animals/{registered_animal}/passport")
    assert passport.status_code == 200, passport.text
    body = passport.json()
    rows = {
        row["milking_session"]: row
        for row in body["history"]["milk"]
        if row["animal_id"] == registered_animal
    }
    assert rows["MORNING"]["total_yield"] == 8.0
    assert rows["AFTERNOON"]["total_yield"] == 7.0
    assert rows["EVENING"]["total_yield"] == 6.0
    assert body["production"]["lifetime"]["lifetime_milk_liters"] == 21.0


def test_twice_daily_rejects_afternoon_and_accepts_evening(client):
    from dairyos.app import container

    _bind_runtime_operational_state(container)
    created = client.post(
        "/farm/animals",
        json={
            "animal_type": "COW",
            "breed": "HF",
            "lifecycle_status": "LACTATING",
            "is_currently_milking": True,
            "milking_frequency": "TWICE_DAILY",
            "ear_tag": "SIM-TWICE-FREQ-001",
        },
    )
    assert created.status_code == 200, created.text
    animal_id = created.json()["animal_id"]

    body, schedule = _passport_schedule(client, animal_id)
    assert schedule["milking_frequency"] == "TWICE_DAILY", body
    assert schedule["expected_sessions"] == ["MORNING", "EVENING"], body

    morning = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "morning_yield": 9.0,
            "milking_session": "MORNING",
            "operator": "simulation",
        },
    )
    assert morning.status_code == 200, morning.text

    afternoon = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "afternoon_yield": 5.0,
            "milking_session": "AFTERNOON",
            "operator": "simulation",
        },
    )
    assert afternoon.status_code == 409, afternoon.text
    assert "AFTERNOON" in afternoon.text

    evening = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "evening_yield": 8.0,
            "milking_session": "EVENING",
            "operator": "simulation",
        },
    )
    assert evening.status_code == 200, evening.text

    final_passport = client.get(f"/farm/animals/{animal_id}/passport")
    assert final_passport.status_code == 200, final_passport.text
    body = final_passport.json()
    assert body["schedule"]["milking_frequency"] == "TWICE_DAILY"
    assert body["schedule"]["expected_sessions"] == ["MORNING", "EVENING"]
    rows = [
        row
        for row in body["history"]["milk"]
        if row["animal_id"] == animal_id
    ]
    sessions = {row["milking_session"] for row in rows}
    assert sessions == {"MORNING", "EVENING"}
    assert body["production"]["lifetime"]["lifetime_milk_liters"] == 17.0
