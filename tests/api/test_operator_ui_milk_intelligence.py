from fastapi.testclient import TestClient

from pathlib import Path

from dairyos.app import app


REPO_ROOT = Path(__file__).resolve().parents[2]
SHELL = REPO_ROOT / "src" / "DairyOS.Web" / "src" / "ui" / "DairyOSShell.tsx"


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


def test_milk_intelligence_is_represented_by_active_operator_shell(client: TestClient):
    root = client.get("/")
    assert root.status_code == 200
    body = root.json()
    assert body["operator_ui"]["authoritative"] is True
    assert body["legacy_static_ui"]["served"] is False

    source = SHELL.read_text(encoding="utf-8")
    assert "animal yield alerts above 20% drop" in source
    assert "Open alerts" in source
    assert "/farm/milk/intelligence" in source or "/farm/milk" in source
