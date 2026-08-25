from fastapi.testclient import TestClient


def test_login_issues_signed_admin_token(client: TestClient, monkeypatch):
    monkeypatch.setenv("DAIRYOS_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("DAIRYOS_ADMIN_PASSWORD", "test-password")
    monkeypatch.setenv("DAIRYOS_ADMIN_ROLE", "operator")  # ignored by design: bootstrap identity is always ADMIN
    monkeypatch.setenv("DAIRYOS_AUTH_SECRET", "test-secret")

    response = client.post(
        "/login",
        json={"username": "admin", "password": "test-password"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["user"] == {"username": "admin", "role": "ADMIN"}
    assert payload["access_token"] != "static-token"

    me = client.get(
        "/me",
        headers={"Authorization": f"Bearer {payload['access_token']}"},
    )

    assert me.status_code == 200
    assert me.json()["username"] == "admin"
    assert me.json()["role"] == "ADMIN"


def test_login_rejects_invalid_credentials(client: TestClient, monkeypatch):
    monkeypatch.setenv("DAIRYOS_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("DAIRYOS_ADMIN_PASSWORD", "test-password")

    response = client.post(
        "/login",
        json={"username": "admin", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_me_requires_authentication(client: TestClient):
    response = client.get("/me")

    assert response.status_code == 401


def test_me_rejects_tampered_token(client: TestClient, monkeypatch):
    monkeypatch.setenv("DAIRYOS_AUTH_SECRET", "test-secret")

    response = client.get(
        "/me",
        headers={"Authorization": "Bearer invalid.token"},
    )

    assert response.status_code == 401
