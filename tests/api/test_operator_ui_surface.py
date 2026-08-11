"""
DairyOS Operator Cockpit UI contract tests.

Version: 0.3.1
Date: 2026-08-11
Purpose: lock the five-prime-part dashboard information architecture,
persistent exception rail, customization/reorder controls, role-aware
persistence bridge, and live domain entry surface.
"""

from fastapi.testclient import TestClient

from dairyos.app import app


DOMAIN_ENDPOINTS = {
    "milk": "/farm/milk",
    "feed": "/farm/feed",
    "health-observations": "/farm/health-observations",
    "breeding": "/farm/breeding",
    "financial": "/farm/financial",
}


def test_operator_dashboard_is_reachable(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200
    html = response.text

    assert "DairyOS" in html
    assert "Today at a glance" in html
    assert "Exceptions & attention — always visible" in html

    for label in (
        "Herd Management",
        "Milk Records",
        "Health & Vaccination",
        "Feed Management",
        "Financials",
    ):
        assert label in html


def test_operator_ui_static_entrypoint_is_reachable(client: TestClient):
    response = client.get("/ui/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_dashboard_has_non_hideable_exception_and_customization_contract(
    client: TestClient,
):
    html = client.get("/").text

    assert "global-alert-rail" in html
    assert "Exceptions & attention — always visible" in html
    assert "function renderAlerts()" in html
    assert "function customize(id)" in html
    assert "function resetSection(id)" in html
    assert "function resetDashboard()" in html
    assert "dairyos.dashboard.widgets" in html
    assert "/ui/dashboard_enhancements.js" in html
    assert "widget-order-row" in html
    assert "Move up" in html
    assert "Move down" in html


def test_dashboard_preserves_five_prime_sections_as_permanent_structure(
    client: TestClient,
):
    html = client.get("/").text

    assert "const PRIME=[" in html
    assert "id:'herd'" in html
    assert "id:'milk'" in html
    assert "id:'health'" in html
    assert "id:'feed'" in html
    assert "id:'finance'" in html
    assert "prime-section full" in html
    assert "The section itself can never disappear." in html
    assert "function sectionCard(s,body)" in html


def test_dashboard_has_operational_drill_down_and_domain_navigation(
    client: TestClient,
):
    html = client.get("/").text

    for domain in ("herd", "milk", "health", "feed", "finance", "breeding"):
        assert f"openPage('{domain}')" in html

    for endpoint in DOMAIN_ENDPOINTS.values():
        assert endpoint in html

    assert "Record event" in html
    assert "Record milk" in html
    assert "Record feed" in html


def test_dashboard_has_evidence_based_analytics_boundaries(client: TestClient):
    html = client.get("/").text

    assert "No forecast is invented" in html
    assert "not yet computable" in html
    assert "No synthetic values" not in html or "measured quality data" in html
    assert "evidence-based" in html
    assert "does not fabricate animal records" in html


def test_operational_presentation_and_api_surface_are_reachable(
    client: TestClient,
):
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


def test_all_current_operational_data_entry_workflows_are_usable(
    client: TestClient,
):
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
