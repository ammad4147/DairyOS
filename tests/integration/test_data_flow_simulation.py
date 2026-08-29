"""Public-entry-point milk flow simulations.

These tests use operator-facing APIs and read the authoritative Animal
Passport before asserting downstream state. A failed Passport request must
surface its actual HTTP error rather than masquerading as a missing history
key.
"""


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


def test_thrice_daily_animal_requires_all_three_passport_sessions(
    client,
    registered_animal,
):
    _runtime(client)
    frequency, expected = _schedule(client, registered_animal)
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
                "animal_id": registered_animal,
                field: value,
                "milking_session": session,
                "operator": "simulation",
            },
        )
        assert response.status_code == 200, response.text

    day = _schedule(client, registered_animal)[0]
    assert day == "THRICE_DAILY"

    _, passport = _milk_row(
        client,
        registered_animal,
        _passport_day(client, registered_animal),
    )
    rows = {
        row["milking_session"]: row
        for row in passport["history"]["milk"]
        if row["animal_id"] == registered_animal
    }
    assert rows["MORNING"]["total_yield"] == 8.0
    assert rows["AFTERNOON"]["total_yield"] == 7.0
    assert rows["EVENING"]["total_yield"] == 6.0
    assert passport["production"]["lifetime"]["lifetime_milk_liters"] == 21.0


def _passport_day(client, animal_id):
    response = client.get(f"/farm/animals/{animal_id}/passport")
    assert response.status_code == 200, response.text
    body = response.json()
    assert "schedule" in body, body
    return body["schedule"]["effective"]["operational_date"]


def test_twice_daily_animal_never_requires_afternoon(client):
    _runtime(client)
    animal_id = _register(client, "TWICE_DAILY")
    frequency, expected = _schedule(client, animal_id)
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
    assert "AFTERNOON" in afternoon.text

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

    row, _ = _milk_row(client, animal_id, _passport_day(client, animal_id))
    assert row["morning_yield"] == 8.0
    assert row["afternoon_yield"] is None
    assert row["evening_yield"] == 6.0
    assert row["total_yield"] == 14.0
