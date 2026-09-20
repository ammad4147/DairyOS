from pathlib import Path

from dairyos.api import breeding_biology
from dairyos.api.animal_management import reproduction as animal_reproduction
from tests.helpers.breeding import ensure_test_semen_lot, post_breeding


def test_duplicate_compatibility_routes_are_not_mounted_as_public_authorities():
    app_source = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "dairyos"
        / "app.py"
    ).read_text(encoding="utf-8")

    assert '_unmount_duplicate_routes(farm_router, {"/farm/breeding"})' in app_source
    assert (
        '_unmount_duplicate_routes(breeding_biology_router, {"/dashboard"})'
        in app_source
    )


def test_event_only_root_write_routes_are_not_public_authorities():
    command_center_source = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "dairyos"
        / "api"
        / "command_center.py"
    ).read_text(encoding="utf-8")

    assert '@router.post("/animals")' not in command_center_source
    assert '@router.post("/milk")' not in command_center_source
    assert '@router.post("/feed")' not in command_center_source


def test_production_reproductive_policies_use_283_day_gestation():
    assert breeding_biology._POLICY.gestation_days == 283
    assert animal_reproduction._POLICY.gestation_days == 283


def _heifer(client, ear_tag):
    response = client.post(
        "/farm/animals",
        json={
            "animal_type": "CATTLE",
            "animal_category": "Heifer",
            "ear_tag": ear_tag,
            "breed": "Sahiwal",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["animal_id"]


def _breed(client, animal_id, event_type, result):
    response = post_breeding(
        client,
        animal_id,
        event_type,
        result,
        technician="AUDIT-TECH",
        operator="AUDIT-TECH",
    )
    assert response.status_code == 200, response.text
    return response


def test_dashboard_reproduction_current_states_are_mutually_exclusive(client):
    pending_id = _heifer(client, "AUDIT-PENDING-001")
    pregnant_id = _heifer(client, "AUDIT-PREGNANT-001")

    _breed(client, pending_id, "insemination", "COMPLETED")
    _breed(client, pregnant_id, "insemination", "COMPLETED")
    _breed(client, pregnant_id, "pregnancy_confirmed", "POSITIVE")

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200, dashboard.text
    reproduction = dashboard.json()["reproduction"]

    assert reproduction["inseminated"] == 1
    assert reproduction["pregnant"] == 1
    # The Dashboard uses the canonical observed conception metric.
    assert reproduction["pregnancyRatio"] == 100.0
    assert reproduction["pregnancy_ratio_percent"] == 100.0


def test_three_ai_two_positive_pd_reconciles_dashboard_and_breeding_analytics(client):
    animals = [_heifer(client, f"AUDIT-3AI-{index}") for index in range(1, 4)]
    lot = ensure_test_semen_lot(client, sire_code="AUDIT-3AI-SIRE", quantity=3)

    for animal_id in animals:
        response = post_breeding(
            client,
            animal_id,
            "insemination",
            "COMPLETED",
            semen_lot_id=lot["id"],
        )
        assert response.status_code == 200, response.text

    for animal_id, result in zip(animals, ("POSITIVE", "POSITIVE", "NEGATIVE")):
        response = post_breeding(
            client,
            animal_id,
            "pregnancy_confirmed" if result == "POSITIVE" else "pregnancy_negative",
            result,
        )
        assert response.status_code == 200, response.text

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200, dashboard.text
    dashboard_reproduction = dashboard.json()["reproduction"]

    analytics = client.get("/farm/reproduction/analytics")
    assert analytics.status_code == 200, analytics.text
    analytics_body = analytics.json()

    assert dashboard_reproduction["pregnancyRatio"] == 66.67
    assert analytics_body["herd_conception_rate_percent"] == 66.67
    assert dashboard_reproduction["pregnant"] == 2
    assert dashboard_reproduction["inseminated"] == 0

    stock = client.get("/farm/breeding/semen-stock")
    assert stock.status_code == 200, stock.text
    audit_lot = next(row for row in stock.json()["lots"] if row["id"] == lot["id"])
    assert audit_lot["available_straws"] == 0
