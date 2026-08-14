"""Authoritative operator UI and operational API contract tests.

The authoritative operator surface is the React/Vite application under
``src/DairyOS.Web``. FastAPI is the API/runtime surface and must not expose the
retired static operator UI.
"""

from pathlib import Path

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = REPO_ROOT / "src" / "DairyOS.Web" / "src"
APP_TSX = WEB_ROOT / "App.tsx"
SHELL_TSX = WEB_ROOT / "ui" / "DairyOSShell.tsx"
FASTAPI_APP = REPO_ROOT / "src" / "dairyos" / "app.py"
LEGACY_UI_ENTRYPOINT = REPO_ROOT / "src" / "dairyos" / "web" / "index.html"

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


def test_legacy_static_operator_surface_is_retired(client: TestClient):
    assert not LEGACY_UI_ENTRYPOINT.exists()
    response = client.get("/ui/")
    assert response.status_code == 404
    source = FASTAPI_APP.read_text(encoding="utf-8")
    assert "StaticFiles" not in source
    assert "WEB_DIR" not in source
    assert "app.mount(\"/ui\"" not in source


def test_active_operator_shell_contains_approved_navigation():
    source = _active_shell()
    assert "DairyOSShell" in source
    for label in (
        "Dashboard", "Animals", "Milk", "Feeding", "Health", "Breeding",
        "Workforce", "Inventory", "Equipment", "Finance", "Analytics",
        "Alerts", "Settings",
    ):
        assert f'label: "{label}"' in source or f'<span>{label}</span>' in source


def test_active_shell_preserves_approved_dashboard_contract():
    source = _active_shell()
    assert 'type Period = "7d" | "month" | "year" | "custom"' in source
    assert 'type FinanceView = "cash" | "bank" | "monthly" | "quarterly" | "yearly"' in source
    assert "Herd Composition" in source
    assert "Milk Production" in source
    assert "Quick Access" in source
    assert "SettingsPage" in source


def test_active_shell_uses_live_domain_endpoints():
    source = _active_shell()
    for endpoint in DOMAIN_ENDPOINTS.values():
        assert endpoint in source


def test_active_shell_uses_meaningful_domain_choices():
    source = _active_shell()
    for value in (
        "CATTLE", "BUFFALO", "LACTATING", "THRICE_DAILY", "MORNING",
        "SILAGE", "pregnancy_confirmed", "EXPENSE", "CASH", "BANK",
    ):
        assert value in source

    assert 'source: "breeds"' in source
    assert 'source: "animals"' in source
    assert 'source: "workers"' in source
    assert 'source: "inventory"' in source
    assert 'source: "equipment"' in source
    assert 'source: "locations"' in source


def test_operational_presentation_and_api_surface_are_reachable(client: TestClient):
    for path in ("/health", "/readiness", "/version", "/dashboard", "/command-center"):
        response = client.get(path)
        assert response.status_code == 200, (path, response.text)
        assert response.headers["content-type"].startswith("application/json")


def test_unknown_animal_id_is_rejected_before_operational_write(client: TestClient):
    for path, payload in (
        ("/farm/milk", {"animal_id": "NOT-A-REAL-ANIMAL", "morning_yield": 1}),
        ("/farm/health-observations", {"animal_id": "NOT-A-REAL-ANIMAL", "symptom": "test"}),
        ("/farm/treatments", {"animal_id": "NOT-A-REAL-ANIMAL", "medicine": "test", "milk_withdrawal_days": 1}),
        ("/farm/breeding", {"animal_id": "NOT-A-REAL-ANIMAL", "event_type": "heat_detected"}),
    ):
        response = client.post(path, json=payload)
        assert response.status_code == 422, (path, response.text)
        assert "Unknown Animal ID" in response.text


def test_all_current_operational_data_entry_workflows_are_usable(client: TestClient):
    animal_response = client.post(
        "/farm/animals",
        json={
            "animal_type": "COW",
            "breed": "Sahiwal",
            "lifecycle_status": "LACTATING",
            "is_currently_milking": True,
            "milking_frequency": "THRICE_DAILY",
        },
    )
    assert animal_response.status_code == 200, animal_response.text
    animal_id = animal_response.json()["animal_id"]
    payloads = {
        "/farm/milk": {"animal_id": animal_id, "morning_yield": 8, "afternoon_yield": 7, "evening_yield": 6, "operator": "UI-Test"},
        "/farm/feed": {"feed_type": "Silage", "quantity_kg": 25, "group_or_pen": "Pen A", "operator": "UI-Test"},
        "/farm/health-observations": {"animal_id": animal_id, "symptom": "Normal", "severity": "LOW", "operator": "UI-Test"},
        "/farm/breeding": {"animal_id": animal_id, "event_type": "insemination", "technician": "Dr Vet", "result": "completed", "operator": "UI-Test"},
        "/farm/financial": {"transaction_type": "EXPENSE", "amount": 1000, "category": "FEED", "payment_method": "CASH", "operator": "UI-Test"},
    }
    for path, payload in payloads.items():
        response = client.post(path, json=payload)
        assert response.status_code in (200, 201), (path, response.text)
        read_response = client.get(path)
        assert read_response.status_code == 200, (path, read_response.text)
        assert isinstance(read_response.json(), list)
