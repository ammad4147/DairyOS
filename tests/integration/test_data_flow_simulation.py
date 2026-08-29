"""Entry-point-driven data-flow simulations.

These tests deliberately use public operator entry points rather than direct
model insertion. Each simulation reads the animal's persisted Passport
schedule first, so twice-daily and thrice-daily animals are never conflated.
"""


def _bind_runtime_operational_state(container):
    container.runtime._operational_input_projection_bridge.state_service = (
        container.runtime._operational_state_service
    )
    if getattr(container, "operational_command_center_service", None) is not None:
        container.operational_command_center_service.operational_state_service = (
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


def _passport_schedule(client, animal_id, as_of_date=None):
    params = {"as_of_date": as_of_date} if as_of_date else None
    response = client.get(
        f"/farm/animals/{animal_id}/passport",
        params=params,
    )
    assert response.status_code == 200, response.text
    passport = response.json()
    effective = (passport.get("schedule") or {}).get("effective") or {}
    frequency = effective.get("milking_frequency")
    expected = effective.get("expected_sessions")
    assert frequency in {"TWICE_DAILY", "THRICE_DAILY"}
    assert expected
    return passport, frequency, expected


def test_milk_entry_flows_to_animal_passport_and_operations_dashboard(
    client,
    registered_animal,
):
    from dairyos.app import container

    _bind_runtime_operational_state(container)
    _, frequency, expected = _passport_schedule(client, registered_animal)
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


def test_thrice_daily_animal_requires_all_three_passport_sessions(client):
    from dairyos.app import container

    _bind_runtime_operational_state(container)
    animal_id = _register_scheduled_animal(client, "THRICE_DAILY")
    _, frequency, expected = _passport_schedule(client, animal_id)
    assert frequency == "THRICE_DAILY"
    assert expected == ["MORNING", "AFTERNOON", "EVENING"]

    for session, field, value in (
        ("MORNING", "morning_yield", 8.0),
        ("AFTERNOON", "afternoon_yield", 7.0),
        ("EVENING", "evening_yield", 6.0),
    ):
        response = client.post(
            "/farm/milk",
            json={
                "animal_id": animal_id,
                field: value,
                "milking_session": session,
                "operator": "simulation",
            },
        )
        assert response.status_code == 200, response.text

    passport = client.get(f"/farm/animals/{animal_id}/passport")
    assert passport.status_code == 200, passport.text
    data = passport.json()
    _, _, expected_again = _passport_schedule(client, animal_id)
    assert data["schedule"]["effective"]["expected_sessions"] == expected_again
    rows = [
        row for row in data["history"]["milk"]
        if row["animal_id"] == animal_id
    ]
    by_session = {row["milking_session"]: row for row in rows}
    assert by_session["MORNING"]["total_yield"] == 8.0
    assert by_session["AFTERNOON"]["total_yield"] == 7.0
    assert by_session["EVENING"]["total_yield"] == 6.0
    assert sum(row["total_yield"] for row in rows) == 21.0


def test_twice_daily_animal_never_requires_afternoon(client):
    from dairyos.app import container

    _bind_runtime_operational_state(container)
    animal_id = _register_scheduled_animal(client, "TWICE_DAILY")
    _, frequency, expected = _passport_schedule(client, animal_id)
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
    assert data["schedule"]["effective"]["milking_frequency"] == "TWICE_DAILY"
    assert data["schedule"]["effective"]["expected_sessions"] == expected
    rows = [
        row
        for row in data["history"]["milk"]
        if row["animal_id"] == animal_id
    ]
    assert {row["milking_session"] for row in rows} == {
        "MORNING",
        "EVENING",
    }
    assert sum(row["total_yield"] for row in rows) == 14.0


def test_individual_passport_schedule_transition_changes_allowed_sessions(client):
    from dairyos.app import container

    _bind_runtime_operational_state(container)
    animal_id = _register_scheduled_animal(client, "THRICE_DAILY")
    _, initial_frequency, initial_sessions = _passport_schedule(client, animal_id)
    assert initial_frequency == "THRICE_DAILY"
    assert initial_sessions == ["MORNING", "AFTERNOON", "EVENING"]

    future_date = "2099-01-02"
    change = client.post(
        f"/farm/animals/{animal_id}/milking-frequency",
        json={
            "milking_frequency": "TWICE_DAILY",
            "changed_by": "simulation",
            "reason": "Simulation schedule transition",
            "effective_date": future_date,
        },
    )
    assert change.status_code == 200, change.text

    _, historical_frequency, historical_sessions = _passport_schedule(
        client, animal_id, as_of_date="2099-01-01"
    )
    assert historical_frequency == "THRICE_DAILY"
    assert historical_sessions == ["MORNING", "AFTERNOON", "EVENING"]

    _, future_frequency, future_sessions = _passport_schedule(
        client, animal_id, as_of_date=future_date
    )
    assert future_frequency == "TWICE_DAILY"
    assert future_sessions == ["MORNING", "EVENING"]

    morning = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "morning_yield": 9.0,
            "milking_session": "MORNING",
            "production_date": future_date,
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
            "production_date": future_date,
            "operator": "simulation",
        },
    )
    assert afternoon.status_code == 409, afternoon.text
    assert "AFTERNOON" in str(afternoon.json())

    evening = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "evening_yield": 8.0,
            "milking_session": "EVENING",
            "production_date": future_date,
            "operator": "simulation",
        },
    )
    assert evening.status_code == 200, evening.text

    passport = client.get(
        f"/farm/animals/{animal_id}/passport",
        params={"as_of_date": future_date},
    )
    assert passport.status_code == 200, passport.text
    data = passport.json()
    assert data["schedule"]["effective"]["milking_frequency"] == "TWICE_DAILY"
    assert data["schedule"]["effective"]["expected_sessions"] == ["MORNING", "EVENING"]
    future_rows = [
        row
        for row in data["history"]["milk"]
        if row["animal_id"] == animal_id
        and row["production_date"].startswith(future_date)
    ]
    assert {row["milking_session"] for row in future_rows} == {
        "MORNING",
        "EVENING",
    }
    assert sum(row["total_yield"] for row in future_rows) == 17.0


def test_milk_entry_simulation_does_not_fabricate_an_unsettled_session(
    client,
    registered_animal,
):
    from dairyos.app import container

    _bind_runtime_operational_state(container)
    _, frequency, expected = _passport_schedule(client, registered_animal)
    assert frequency == "THRICE_DAILY"
    assert expected == ["MORNING", "AFTERNOON", "EVENING"]

    blocked = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "afternoon_yield": 0.0,
            "milking_session": "AFTERNOON",
            "operator": "simulation",
        },
    )
    assert blocked.status_code == 409, blocked.text
    assert "MORNING" in blocked.text
    assert "has not been recorded or declared" in blocked.text

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
