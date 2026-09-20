import uuid
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = (
    ROOT
    / "src"
    / "DairyOS.Web"
    / "src"
    / "components"
    / "UnifiedDashboard.tsx"
)
CLIENT = (
    ROOT
    / "src"
    / "DairyOS.Web"
    / "src"
    / "api"
    / "commandDashboardClient.ts"
)


def _register(client, frequency: str) -> str:
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "COW",
            "breed": "Sahiwal",
            "sex": "FEMALE",
            "lifecycle_status": "LACTATING",
            "is_currently_milking": True,
            "milking_frequency": frequency,
            "ear_tag": f"PX-{uuid.uuid4().hex[:10].upper()}",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["animal_id"]


def _record_morning(client, animal_id: str, litres: float) -> None:
    response = client.post(
        "/farm/milk",
        json={
            "animal_id": animal_id,
            "production_date": date.today().isoformat(),
            "milking_session": "MORNING",
            "morning_yield": litres,
            "operator": "PRODUCTION-EXTREMES-COHORT-TEST",
        },
    )
    assert response.status_code == 200, response.text


def _litres(rows):
    return [float(row["total_litres"]) for row in rows]


def test_production_extremes_are_ranked_inside_milking_frequency_cohorts(client):
    for litres in (30.0, 20.0, 10.0):
        animal_id = _register(client, "THRICE_DAILY")
        _record_morning(client, animal_id, litres)

    for litres in (18.0, 12.0, 6.0):
        animal_id = _register(client, "TWICE_DAILY")
        _record_morning(client, animal_id, litres)

    response = client.get("/dashboard")
    assert response.status_code == 200, response.text

    extremes = response.json()["milk"]["production_extremes"]
    cohorts = extremes["cohorts"]

    assert extremes["population_count"] == 6
    assert cohorts["THRICE_DAILY"]["population_count"] == 3
    assert cohorts["TWICE_DAILY"]["population_count"] == 3

    assert _litres(cohorts["THRICE_DAILY"]["highest"]) == [30.0]
    assert _litres(cohorts["THRICE_DAILY"]["lowest"]) == [10.0]
    assert _litres(cohorts["TWICE_DAILY"]["highest"]) == [18.0]
    assert _litres(cohorts["TWICE_DAILY"]["lowest"]) == [6.0]

    thrice_ids = {
        row["animal_id"]
        for row in (
            cohorts["THRICE_DAILY"]["highest"]
            + cohorts["THRICE_DAILY"]["lowest"]
        )
    }
    twice_ids = {
        row["animal_id"]
        for row in (
            cohorts["TWICE_DAILY"]["highest"]
            + cohorts["TWICE_DAILY"]["lowest"]
        )
    }
    assert thrice_ids.isdisjoint(twice_ids)


def test_dashboard_extremes_card_has_compact_twice_and_thrice_tabs():
    dashboard = DASHBOARD.read_text(encoding="utf-8")
    client = CLIENT.read_text(encoding="utf-8")

    assert "type ExtremeCohort = 'THRICE_DAILY' | 'TWICE_DAILY'" in dashboard
    assert "useState<ExtremeCohort>('THRICE_DAILY')" in dashboard
    assert "Thrice Milking" in dashboard
    assert "Twice Milking" in dashboard
    assert "data?.productionExtremes?.cohorts?.[extremeCohort]" in dashboard
    assert "<ExtremeList title=\"Highest\" rows={displayedTop}" in dashboard
    assert "<ExtremeList title=\"Lowest\" rows={displayedBottom}" in dashboard
    assert "flex:'0.9 1 0'" in dashboard

    assert "THRICE_DAILY: ProductionExtremeCohort" in client
    assert "TWICE_DAILY: ProductionExtremeCohort" in client
    assert "productionExtremes.cohorts?.THRICE_DAILY" in client
    assert "productionExtremes.cohorts?.TWICE_DAILY" in client
