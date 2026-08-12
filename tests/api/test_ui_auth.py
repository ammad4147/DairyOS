from fastapi.testclient import TestClient


def test_root_declares_react_operator_surface_without_legacy_bridge(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["operator_ui"]["application"] == "DairyOS.Web"
    assert body["operator_ui"]["technology"] == "React/Vite"
    assert body["operator_ui"]["authoritative"] is True
    assert body["legacy_static_ui"]["served"] is False


def test_legacy_ui_auth_bridge_is_not_served(client: TestClient):
    response = client.get("/ui/ui_auth.js")
    assert response.status_code == 404


def test_authenticated_farm_entry_remains_available_on_authoritative_api(
    client: TestClient, monkeypatch, registered_animal
):
    monkeypatch.setenv("DAIRYOS_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("DAIRYOS_ADMIN_PASSWORD", "dairyos")
    monkeypatch.setenv("DAIRYOS_ADMIN_ROLE", "operator")
    monkeypatch.setenv("DAIRYOS_AUTH_SECRET", "test-secret")

    login = client.post(
        "/login",
        json={"username": "admin", "password": "dairyos"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    response = client.post(
        "/farm/milk",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "operator": "ignored-by-server",
            "animal_id": registered_animal,
            "morning_yield": 10,
        },
    )

    assert response.status_code == 200
    assert response.json()["operator"] == "admin"
