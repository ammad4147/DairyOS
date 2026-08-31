"""Approved milk-drop end-to-end acceptance tests only."""

def _activate_deployment(client):
    response = client.post(
        "/settings/deployment/activate",
        json={
            "confirm": "DEPLOY",
            "password": "deploySecret",
        },
    )
    assert response.status_code == 200, response.text


def _set_frequency(client, animal_id, frequency):
    response = client.post(
        f"/farm/animals/{animal_id}/milking-frequency",
        json={
            "milking_frequency": frequency,
            "changed_by": "approved-threshold-test",
            "reason": "Approved milk-drop acceptance test",
            "effective_date": "2026-08-16T00:00:00Z",
        },
    )
    assert response.status_code == 200, response.text


def _milk(client, animal_id, session, field, value, day):
    response = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "milking_session": session,
            field: value,
            "production_date": day,
            "operator": "ApprovedThresholdTester",
        },
    )
    assert response.status_code == 200, response.text


def _find_for_animal(client, animal_id):
    response = client.get(
        "/farm/findings",
        params={"module": "MILK"},
    )
    assert response.status_code == 200, response.text

    return [
        finding
        for finding in response.json()["findings"]
        if finding["subject_id"] == animal_id
    ]


def test_approved_exact_twenty_percent_drop_raises_high(
    client,
    registered_animal,
):
    _activate_deployment(client)
    _set_frequency(
        client,
        registered_animal,
        "TWICE_DAILY",
    )

    # Prior day = 100.0 L.
    _milk(
        client,
        registered_animal,
        "MORNING",
        "morning_yield",
        50.0,
        "2026-08-17",
    )
    _milk(
        client,
        registered_animal,
        "EVENING",
        "evening_yield",
        50.0,
        "2026-08-17",
    )

    # Current day = 80.0 L = exactly 20% decline.
    _milk(
        client,
        registered_animal,
        "MORNING",
        "morning_yield",
        40.0,
        "2026-08-18",
    )
    _milk(
        client,
        registered_animal,
        "EVENING",
        "evening_yield",
        40.0,
        "2026-08-18",
    )

    matching = _find_for_animal(
        client,
        registered_animal,
    )

    assert any(
        finding["severity"] == "HIGH"
        for finding in matching
    ), "expected HIGH finding at exactly 20% decline"


def test_approved_twenty_point_one_percent_drop_raises_critical(
    client,
    registered_animal,
):
    _activate_deployment(client)
    _set_frequency(
        client,
        registered_animal,
        "THRICE_DAILY",
    )

    # Prior day = 100.0 L.
    for session, field, value in (
        ("MORNING", "morning_yield", 50.0),
        ("AFTERNOON", "afternoon_yield", 0.0),
        ("EVENING", "evening_yield", 50.0),
    ):
        _milk(
            client,
            registered_animal,
            session,
            field,
            value,
            "2026-08-17",
        )

    # Current day = 79.9 L = exactly 20.1% decline.
    for session, field, value in (
        ("MORNING", "morning_yield", 39.95),
        ("AFTERNOON", "afternoon_yield", 0.0),
        ("EVENING", "evening_yield", 39.95),
    ):
        _milk(
            client,
            registered_animal,
            session,
            field,
            value,
            "2026-08-18",
        )

    matching = _find_for_animal(
        client,
        registered_animal,
    )

    assert any(
        finding["severity"] == "CRITICAL"
        for finding in matching
    ), (
        "expected CRITICAL finding at exactly "
        "20.1% decline"
    )
