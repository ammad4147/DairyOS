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


def _record_morning(
    client: TestClient,
    animal_id: str,
) -> None:
    response = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "production_date": TODAY.isoformat(),
            "milking_session": "MORNING",
            "morning_yield": 10.0,
            "operator": "NEXT-SESSION-TEST",
        },
    )

    assert response.status_code == 200, response.text


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

    # Before any session has been settled, both animals owe MORNING.
    twice_initial = _next_session(client, twice_daily)
    thrice_initial = _next_session(client, thrice_daily)

    assert twice_initial["operational_date"] == TODAY.isoformat()
    assert thrice_initial["operational_date"] == TODAY.isoformat()

    assert twice_initial["next_session"] == "MORNING"
    assert thrice_initial["next_session"] == "MORNING"

    # Settle the shared MORNING session.
    _record_morning(client, twice_daily)

    # The next session must now be derived from each animal's own schedule:
    # TWICE_DAILY skips AFTERNOON; THRICE_DAILY requires it.
    twice_after_morning = _next_session(client, twice_daily)
    thrice_after_morning = _next_session(client, thrice_daily)

    assert twice_after_morning["next_session"] == "EVENING"
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
