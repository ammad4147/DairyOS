from fastapi.testclient import TestClient

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_SRC = REPO_ROOT / "src" / "DairyOS.Web" / "src"
DASHBOARD = WEB_SRC / "components" / "UnifiedDashboard.tsx"
DASHBOARD_CLIENT = WEB_SRC / "api" / "commandDashboardClient.ts"


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


def test_current_dashboard_represents_persisted_milk_intelligence(client: TestClient):
    root = client.get("/")
    assert root.status_code == 200
    body = root.json()
    assert body["operator_ui"]["authoritative"] is True
    assert body["legacy_static_ui"]["served"] is False

    dashboard = DASHBOARD.read_text(encoding="utf-8-sig")
    dashboard_client = DASHBOARD_CLIENT.read_text(encoding="utf-8-sig")

    assert "Yield Drop Watchlist" in dashboard
    assert "Production Extremes" in dashboard
    assert "yield_drop_watchlist" in dashboard_client
    assert "production_extremes" in dashboard_client
