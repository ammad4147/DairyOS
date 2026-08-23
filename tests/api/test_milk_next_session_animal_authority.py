from datetime import date

from fastapi.testclient import TestClient


TODAY = date(2026, 8, 18)


def _create_animal(
    client: TestClient,
    *,
    frequency: str,
    ear_tag: str,
) -> str:
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "COW",
            "breed": "Sahiwal",
            "lifecycle_status": "LACTATING",
            "is_currently_milking": True,
            "milking_frequency": frequency,
            "ear_tag": ear_tag,
        },
    )

    assert response.status_code == 200, response.text

    payload = response.json()

    assert payload["milking_frequency"] == frequency
    assert payload["is_currently_milking"] is True

    return payload["animal_id"]


def _record_session(
    client: TestClient,
    animal_id: str,
    session: str,
    litres: float,
) -> None:
    payload = {
        "animal_id": animal_id,
        "production_date": TODAY.isoformat(),
        "milking_session": session,
        "morning_yield": litres if session == "MORNING" else None,
        "afternoon_yield": litres if session == "AFTERNOON" else None,
        "evening_yield": litres if session == "EVENING" else None,
        "operator": "NEXT-SESSION-TEST",
    }

    response = client.post(
        "/farm/milk",
        json=payload,
    )

    assert response.status_code == 200, response.text


def _record_morning(
    client: TestClient,
    animal_id: str,
) -> None:
    _record_session(
        client,
        animal_id,
        "MORNING",
        10.0,
    )


def _next_session(
    client: TestClient,
    animal_id: str,
) -> dict:
    response = client.get(
        "/farm/milk/next-session",
        params={
            "operational_date": TODAY.isoformat(),
            "animal_id": animal_id,
        },
    )

    assert response.status_code == 200, response.text

    return response.json()


def test_next_session_uses_effective_frequency_for_specific_animal(
    client: TestClient,
):
    twice_daily = _create_animal(
        client,
        frequency="TWICE_DAILY",
        ear_tag="NEXT-TWICE-001",
    )

    thrice_daily = _create_animal(
        client,
        frequency="THRICE_DAILY",
        ear_tag="NEXT-THRICE-001",
    )

    # Before any animal has been milked, both owe MORNING.
    twice_initial = _next_session(client, twice_daily)
    thrice_initial = _next_session(client, thrice_daily)

    assert twice_initial["operational_date"] == TODAY.isoformat()
    assert thrice_initial["operational_date"] == TODAY.isoformat()

    assert twice_initial["next_session"] == "MORNING"
    assert thrice_initial["next_session"] == "MORNING"

    # Milk only the TWICE_DAILY animal for MORNING.
    _record_morning(client, twice_daily)

    # The TWICE_DAILY animal advances to EVENING.
    twice_after_morning = _next_session(client, twice_daily)

    # The THRICE_DAILY animal is unaffected by the other animal's MORNING.
    thrice_after_other_animal_morning = _next_session(
        client,
        thrice_daily,
    )

    assert twice_after_morning["next_session"] == "EVENING"
    assert thrice_after_other_animal_morning["next_session"] == "MORNING"

    # Now milk the THRICE_DAILY animal for MORNING.
    _record_morning(client, thrice_daily)

    thrice_after_morning = _next_session(
        client,
        thrice_daily,
    )

    assert thrice_after_morning["next_session"] == "AFTERNOON"


def test_next_session_rejects_unknown_animal(
    client: TestClient,
):
    response = client.get(
        "/farm/milk/next-session",
        params={
            "operational_date": TODAY.isoformat(),
            "animal_id": "TD-DOES-NOT-EXIST",
        },
    )

    assert response.status_code in {404, 422}, response.text


def test_next_session_without_animal_id_preserves_farm_level_contract(
    client: TestClient,
):
    response = client.get(
        "/farm/milk/next-session",
        params={
            "operational_date": TODAY.isoformat(),
        },
    )

    assert response.status_code == 200, response.text

    payload = response.json()

    assert payload["operational_date"] == TODAY.isoformat()
    assert "next_session" in payload
    assert "observed_sessions" in payload
    assert "settled_sessions" in payload
