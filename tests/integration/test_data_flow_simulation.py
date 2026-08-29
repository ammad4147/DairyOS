"""Public-entry-point milk flow simulations."""


def _runtime(client):
    from dairyos.app import container

    container.runtime._operational_input_projection_bridge.state_service = (
        container.runtime._operational_state_service
    )
    if getattr(container, "operational_command_center_service", None) is not None:
        container.operational_command_center_service.operational_state_service = (
            container.runtime._operational_state_service
        )
    return container


def _schedule(client, animal_id, as_of_date=None):
    response = client.get(
        f"/farm/animals/{animal_id}/passport",
        params={"as_of_date": as_of_date} if as_of_date else None,
    )
    assert response.status_code == 200, response.text
    effective = response.json()["schedule"]["effective"]
    return effective["milking_frequency"], effective["expected_sessions"]


def _register(client, frequency):
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


def _passport(client, animal_id, production_date):
    response = client.get(
        f"/farm/animals/{animal_id}/passport",
        params={"as_of_date": production_date},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "history" in body, body
    assert "milk" in body["history"], body
    return body


def _operational_date(container):
    from dairyos.farm.settings.services.operational_date_authority import (
        OperationalDateAuthority,
    )

    return OperationalDateAuthority(
        repository_factory=container.repository_factory,
    ).current_date().isoformat()


def _milk_row(client, animal_id, production_date):
    body = _passport(client, animal_id, production_date)
    rows = [
        row
        for row in body["history"]["milk"]
        if row["animal_id"] == animal_id
        and str(row["production_date"]).startswith(production_date)
    ]
    assert len(rows) == 1, rows
    return rows[0], body


def test_milk_entry_flows_to_animal_passport_and_operations_dashboard(
    client,
    registered_animal,
):
    container = _runtime(client)
    frequency, expected = _schedule(client, registered_animal)
    assert frequency == "THRICE_DAILY"
    assert expected == ["MORNING", "AFTERNOON", "EVENING"]
    day = _operational_date(container)

    response = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "morning_yield": 8.0,
            "milking_session": "MORNING",
            "production_date": day,
            "operator": "simulation",
        },
    )
    assert response.status_code == 200, response.text
    row, passport = _milk_row(client, registered_animal, day)
    assert row["morning_yield"] == 8.0
    assert row["afternoon_yield"] is None
    assert row["evening_yield"] is None
    assert passport["production"]["lifetime"]["lifetime_milk_liters"] == 8.0

    operations = client.get("/operations/dashboard")
    assert operations.status_code == 200, operations.text
    assert operations.json()["milk_today"] == 8.0


def test_thrice_daily_animal_requires_all_three_passport_sessions(
    client,
    registered_animal,
):
    container = _runtime(client)
    frequency, expected = _schedule(client, registered_animal)
    assert frequency == "THRICE_DAILY"
    assert expected == ["MORNING", "AFTERNOON", "EVENING"]
    day = _operational_date(container)

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
                "production_date": day,
                "operator": "simulation",
            },
        )
        assert response.status_code == 200, response.text

    row, passport = _milk_row(client, registered_animal, day)
    assert (
        row["morning_yield"],
        row["afternoon_yield"],
        row["evening_yield"],
        row["total_yield"],
    ) == (8.0, 7.0, 6.0, 21.0)
    assert passport["production"]["lifetime"]["lifetime_milk_liters"] == 21.0


def test_twice_daily_animal_never_requires_afternoon(client):
    container = _runtime(client)
    animal_id = _register(client, "TWICE_DAILY")
    frequency, expected = _schedule(client, animal_id)
    assert frequency == "TWICE_DAILY"
    assert expected == ["MORNING", "EVENING"]
    day = _operational_date(container)

    morning = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "morning_yield": 8.0,
            "milking_session": "MORNING",
            "production_date": day,
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
            "production_date": day,
            "operator": "simulation",
        },
    )
    assert afternoon.status_code == 409, afternoon.text
    assert "AFTERNOON" in afternoon.text

    evening = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "evening_yield": 6.0,
            "milking_session": "EVENING",
            "production_date": day,
            "operator": "simulation",
        },
    )
    assert evening.status_code == 200, evening.text

    row, _ = _milk_row(client, animal_id, day)
    assert row["morning_yield"] == 8.0
    assert row["afternoon_yield"] is None
    assert row["evening_yield"] == 6.0
    assert row["total_yield"] == 14.0


def test_individual_passport_schedule_transition_changes_allowed_sessions(client):
    container = _runtime(client)
    animal_id = _register(client, "THRICE_DAILY")
    _, initial_sessions = _schedule(client, animal_id)
    assert initial_sessions == ["MORNING", "AFTERNOON", "EVENING"]

    future = "2099-01-02"
    change = client.post(
        f"/farm/animals/{animal_id}/milking-frequency",
        json={
            "milking_frequency": "TWICE_DAILY",
            "changed_by": "simulation",
            "reason": "Simulation schedule transition",
            "effective_date": future,
        },
    )
    assert change.status_code == 200, change.text
    assert _schedule(client, animal_id, "2099-01-01")[1] == [
        "MORNING",
        "AFTERNOON",
        "EVENING",
    ]
    assert _schedule(client, animal_id, future)[1] == ["MORNING", "EVENING"]

    morning = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "morning_yield": 9.0,
            "milking_session": "MORNING",
            "production_date": future,
            "operator": "simulation",
        },
    )
    assert morning.status_code == 200, morning.text
    blocked = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "afternoon_yield": 7.0,
            "milking_session": "AFTERNOON",
            "production_date": future,
            "operator": "simulation",
        },
    )
    assert blocked.status_code == 409, blocked.text
    assert "AFTERNOON" in blocked.text
    evening = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "evening_yield": 8.0,
            "milking_session": "EVENING",
            "production_date": future,
            "operator": "simulation",
        },
    )
    assert evening.status_code == 200, evening.text
    row, _ = _milk_row(client, animal_id, future)
    assert row["morning_yield"] == 9.0
    assert row["afternoon_yield"] is None
    assert row["evening_yield"] == 8.0
    assert row["total_yield"] == 17.0


def test_milk_entry_simulation_does_not_fabricate_an_unsettled_session(
    client,
    registered_animal,
):
    _runtime(client)
    assert _schedule(client, registered_animal)[1] == [
        "MORNING",
        "AFTERNOON",
        "EVENING",
    ]
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
