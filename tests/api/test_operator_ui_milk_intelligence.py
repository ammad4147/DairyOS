from fastapi.testclient import TestClient

from dairyos.app import app


def test_milk_intelligence_endpoint_is_reachable(client: TestClient):
    response = client.get("/farm/milk/intelligence")

    assert response.status_code == 200, response.text
    payload = response.json()

    for key in (
        "yesterday_litres",
        "seven_day_average_litres",
        "seven_day_total_litres",
        "daily_trend",
        "animal_ranking",
        "yield_drop_threshold_percent",
        "yield_drop_alerts",
    ):
        assert key in payload


def test_milk_intelligence_bridge_is_loaded_by_operator_root(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200
    assert "/ui/dashboard_milk_intelligence.js" in response.text
    assert "Evidence-based milk intelligence" in client.get(
        "/ui/dashboard_milk_intelligence.js"
    ).text
    assert "No synthetic values" in client.get(
        "/ui/dashboard_live.js"
    ).text
