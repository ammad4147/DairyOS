from pathlib import Path

from dairyos.api import breeding_biology
from dairyos.api.animal_management import reproduction as animal_reproduction
from tests.helpers.breeding import post_breeding


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
    assert reproduction["pregnancyRatio"] == 50.0
    assert reproduction["pregnancy_ratio_percent"] == 50.0
