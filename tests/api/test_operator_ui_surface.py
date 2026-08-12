"""Operator UI and operational API contract tests.

The authoritative operator surface is the React/Vite application under
``src/DairyOS.Web``. FastAPI is the API/runtime surface and must not serve
or validate the retired static dashboard.
"""

from pathlib import Path

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = REPO_ROOT / "src" / "DairyOS.Web" / "src"
APP_TSX = WEB_ROOT / "App.tsx"
SHELL_TSX = WEB_ROOT / "ui" / "DairyOSShell.tsx"

DOMAIN_ENDPOINTS = {
    "milk": "/farm/milk",
    "feed": "/farm/feed",
    "health-observations": "/farm/health-observations",
    "breeding": "/farm/breeding",
    "financial": "/farm/financial",
}


def _active_shell() -> str:
    assert APP_TSX.exists(), f"Active frontend entrypoint missing: {APP_TSX}"
    assert SHELL_TSX.exists(), f"Active operator shell missing: {SHELL_TSX}"
    return APP_TSX.read_text(encoding="utf-8") + "\n" + SHELL_TSX.read_text(encoding="utf-8")


def test_operator_api_root_declares_react_as_authoritative(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["system"] == "DairyOS"
    assert body["surface"] == "api"
    assert body["operator_ui"]["application"] == "DairyOS.Web"
    assert body["operator_ui"]["technology"] == "React/Vite"
    assert body["operator_ui"]["authoritative"] is True
    assert body["legacy_static_ui"]["served"] is False


def test_active_operator_shell_contains_approved_navigation():
    source = _active_shell()
    assert "DairyOSShell" in source
    for label in ("Dashboard", "Animals", "Milk", "Feeding", "Health", "Breeding", "Workforce", "Inventory", "Equipment", "Finance", "Analytics", "Alerts", "Settings"):
        assert f'label: "{label}"' in source or f'label="{label}"' in source


def test_active_shell_preserves_approved_dashboard_contract():
    source = _active_shell()
    assert 'type Period = "7d" | "month" | "year" | "custom"' in source
    assert 'type FinanceView = "cash" | "bank" | "monthly" | "quarterly" | "yearly"' in source
    assert "Herd Composition" in source
    assert "Milk Production" in source
    assert "Quick Access" in source
    assert "Settings" in source


def test_active_shell_uses_live_domain_endpoints():
    source = _active_shell()
    for endpoint in DOMAIN_ENDPOINTS.values():
        assert endpoint in source


def test_active_shell_uses_meaningful_domain_choices():
    source = _active_shell()
    for value in ("CATTLE", "FEMALE", "LACTATING", "THRICE_DAILY", "MORNING", "SILAGE", "PREGNANCY", "EXPENSE", "CASH", "BANK"):
        assert value in source


def test_operational_presentation_and_api_surface_are_reachable(client: TestClient):
    for path in ("/health", "/readiness", "/version", "/dashboard", "/command-center"):
        response = client.get(path)
        assert response.status_code == 200, (path, response.text)
        assert response.headers["content-type"].startswith("application/json")


def test_unknown_animal_id_is_rejected_before_operational_write(client: TestClient):
    for path, payload in (
        ("/farm/milk", {"animal_id": "NOT-A-REAL-ANIMAL", "morning_yield": 1}),
        ("/farm/health-observations", {"animal_id": "NOT-A-REAL-ANIMAL", "observation": "test"}),
        ("/farm/treatments", {"animal_id": "NOT-A-REAL-ANIMAL", "medicine": "test", "milk_withdrawal_days": 1}),
        ("/farm/breeding", {"animal_id": "NOT-A-REAL-ANIMAL", "event_type": "heat_detected"}),
    ):
        response = client.post(path, json=payload)
        assert response.status_code == 422, (path, response.text)
        assert "Unknown Animal ID" in response.text


def test_all_current_operational_data_entry_workflows_are_usable(client: TestClient):
    animal_response = client.post("/farm/animals", json={"animal_type": "CATTLE", "sex": "FEMALE", "lifecycle_status": "LACTATING", "breed": "HOLSTEIN", "date_of_birth": "2022-01-01"})
    assert animal_response.status_code in (200, 201), animal_response.text
    animal_id = animal_response.json()["animal_id"]
    payloads = {
        "/farm/milk": {"animal_id": animal_id, "morning_yield": 8, "afternoon_yield": 7, "evening_yield": 6, "operator": "UI-Test"},
        "/farm/feed": {"feed_type": "SILAGE", "quantity_kg": 25, "animal_id": animal_id, "operator": "UI-Test"},
        "/farm/health-observations": {"animal_id": animal_id, "observation": "Normal", "operator": "UI-Test"},
        "/farm/breeding": {"animal_id": animal_id, "event_type": "heat_detected", "operator": "UI-Test"},
        "/farm/financial": {"transaction_type": "EXPENSE", "amount": 1000, "operator": "UI-Test"},
    }
    for path, payload in payloads.items():
        response = client.post(path, json=payload)
        assert response.status_code in (200, 201), (path, response.text)
        read_response = client.get(path)
        assert read_response.status_code == 200, (path, read_response.text)
        assert isinstance(read_response.json(), list)
