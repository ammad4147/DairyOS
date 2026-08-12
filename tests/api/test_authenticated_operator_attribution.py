from fastapi.testclient import TestClient

from dairyos.app import app


client = TestClient(app)


def _login(monkeypatch) -> str:
    monkeypatch.setenv("DAIRYOS_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("DAIRYOS_ADMIN_PASSWORD", "test-password")
    monkeypatch.setenv("DAIRYOS_ADMIN_ROLE", "operator")
    monkeypatch.setenv("DAIRYOS_AUTH_SECRET", "test-secret")

    response = client.post(
        "/login",
        json={"username": "admin", "password": "test-password"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_authenticated_claim_overrides_client_operator_identity(
    monkeypatch, registered_animal
):
    token = _login(monkeypatch)

    response = client.post(
        "/farm/milk",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "operator": "forged-operator",
            "animal_id": registered_animal,
            "morning_yield": 1,
            "afternoon_yield": 2,
            "evening_yield": 3,
        },
    )

    assert response.status_code == 200
    assert response.json()["operator"] == "admin"
    assert response.json()["operator"] != "forged-operator"


def test_unauthenticated_farm_write_preserves_existing_operator_contract(
    registered_animal,
):
    response = client.post(
        "/farm/milk",
        json={
            "operator": "UI Operator",
            "animal_id": registered_animal,
            "morning_yield": 1,
            "afternoon_yield": 2,
            "evening_yield": 3,
        },
    )

    assert response.status_code == 200
    assert response.json()["operator"] == "UI Operator"


def test_invalid_bearer_token_cannot_fall_back_to_client_operator(
    registered_animal,
):
    response = client.post(
        "/farm/milk",
        headers={"Authorization": "Bearer invalid.token"},
        json={
            "operator": "spoofed-client-value",
            "animal_id": registered_animal,
            "morning_yield": 1,
        },
    )

    assert response.status_code == 401


def test_login_issues_identity_bearing_token(monkeypatch):
    token = _login(monkeypatch)
    assert token
