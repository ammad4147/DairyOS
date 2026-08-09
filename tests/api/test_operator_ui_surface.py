from fastapi.testclient import TestClient

from dairyos.app import app



def test_operator_dashboard_is_reachable(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200
    assert "DairyOS" in response.text
    assert "Command Center" in response.text
    assert "Milk" in response.text
    assert "Feeding" in response.text
    assert "Health" in response.text
    assert "Breeding" in response.text
    assert "Workforce" in response.text
    assert "Inventory" in response.text
    assert "Equipment" in response.text
    assert "Finance" in response.text



def test_operator_ui_static_entrypoint_is_reachable(client: TestClient):
    response = client.get("/ui/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")



def test_operational_presentation_and_api_surface_are_reachable(client: TestClient):
    for path in (
        "/health",
        "/readiness",
        "/version",
        "/dashboard",
        "/command-center",
    ):
        response = client.get(path)
        assert response.status_code == 200, (path, response.text)
        assert response.headers["content-type"].startswith("application/json")



def test_all_operational_data_entry_workflows_are_usable(client: TestClient):
    payloads = {
        "/farm/milk": {
            "animal_id": "UI-001",
            "morning_yield": 8,
            "afternoon_yield": 7,
            "evening_yield": 6,
            "operator": "UI-Test",
        },
        "/farm/feed": {
            "feed_type": "TMR",
            "quantity_kg": 25,
            "operator": "UI-Test",
        },
        "/farm/health-observations": {
            "animal_id": "UI-001",
            "observation": "Normal",
            "operator": "UI-Test",
        },
        "/farm/breeding": {
            "animal_id": "UI-001",
            "event_type": "HEAT_OBSERVED",
            "operator": "UI-Test",
        },
        "/farm/workforce": {
            "worker_id": "W-001",
            "activity": "Milking",
            "operator": "UI-Test",
        },
        "/farm/inventory": {
            "item": "Feed",
            "quantity": 100,
            "operator": "UI-Test",
        },
        "/farm/equipment": {
            "equipment_id": "EQ-001",
            "activity": "Inspection",
            "operator": "UI-Test",
        },
        "/farm/financial": {
            "transaction_type": "EXPENSE",
            "amount": 1000,
            "operator": "UI-Test",
        },
    }

    for path, payload in payloads.items():
        response = client.post(path, json=payload)
        assert response.status_code == 200, (path, response.text)

        read_response = client.get(path)
        assert read_response.status_code == 200, (path, read_response.text)
        assert isinstance(read_response.json(), list)
