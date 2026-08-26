from fastapi.testclient import TestClient


def _login(client: TestClient, monkeypatch) -> str:
    monkeypatch.setenv("DAIRYOS_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("DAIRYOS_ADMIN_PASSWORD", "test-password")
    monkeypatch.setenv("DAIRYOS_ADMIN_ROLE", "operator")
    monkeypatch.setenv("DAIRYOS_AUTH_SECRET", "test-secret")

    response = client.post("/login", json={"username": "admin", "password": "test-password"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_authenticated_data_entry_uses_server_identity(client: TestClient, monkeypatch, registered_animal):
    token = _login(client, monkeypatch)
    response = client.post(
        "/farm/milk",
        headers={"Authorization": f"Bearer {token}"},
        json={"operator": "spoofed-client-value", "animal_id": registered_animal, "morning_yield": 10, "afternoon_yield": 8, "evening_yield": 7},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["operator"] == "admin"
    assert payload["litres"] == 25
    assert payload["total_yield"] == 25


def test_unauthenticated_data_entry_preserves_operator_contract(client: TestClient, registered_animal):
    # The shared fixture authenticates the TestClient for most API tests. Remove
    # that identity explicitly so this test exercises the documented development
    # fallback rather than accidentally testing an authenticated request.
    client.headers.pop("Authorization", None)
    response = client.post(
        "/farm/milk",
        json={"operator": "UI Operator", "animal_id": registered_animal, "morning_yield": 5, "afternoon_yield": 4, "evening_yield": 3},
    )
    assert response.status_code == 200
    assert response.json()["operator"] == "UI Operator"


def test_invalid_bearer_token_cannot_fall_back_to_client_operator(client: TestClient, registered_animal):
    response = client.post(
        "/farm/milk",
        headers={"Authorization": "Bearer invalid.token"},
        json={"operator": "spoofed-client-value", "animal_id": registered_animal, "morning_yield": 1},
    )
    assert response.status_code == 401
