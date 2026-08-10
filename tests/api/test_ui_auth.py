from fastapi.testclient import TestClient

from dairyos.app import app


def test_root_loads_ui_authentication_bridge():
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert '/ui/ui_auth.js' in response.text


def test_ui_auth_bridge_is_served():
    with TestClient(app) as client:
        response = client.get("/ui/ui_auth.js")

    assert response.status_code == 200
    assert "dairyos.access_token" in response.text
    assert "Authorization" in response.text


def test_authenticated_farm_entry_remains_available_after_ui_bridge_load():
    with TestClient(app) as client:
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
                "animal_id": "UI-AUTH-001",
                "morning_yield": 10,
            },
        )

    assert response.status_code == 200
    assert response.json()["operator"] == "admin"
