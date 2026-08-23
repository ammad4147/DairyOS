from fastapi.testclient import TestClient

from dairyos.app import app


client = TestClient(app)


def test_live_analytics_declares_non_synthetic_backend_authority():
    response = client.get("/farm/analytics-live?days=30")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["synthetic_values"] is False
    assert body["frontend_calculation_authority"] is False
    assert body["period"]["days"] == 30
    assert "milk_environment" in body
    assert "health" in body
    assert "breeding" in body
    assert "financial" in body
    assert "herd_dynamics" in body


def test_live_analytics_rejects_invalid_window():
    response = client.get("/farm/analytics-live?days=0")
    assert response.status_code == 422
