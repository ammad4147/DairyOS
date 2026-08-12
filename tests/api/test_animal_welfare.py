from datetime import datetime, timezone

from dairyos.data.database.models.operational_state_model import OperationalStateModel
from dairyos.data.repositories.repository_factory import RepositoryFactory


def test_welfare_overview_returns_no_data_without_persisted_observations(client):
    response = client.get("/farm/welfare/overview?days=30")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data_status"] == "NO_DATA"
    assert body["observation_count"] == 0
    assert body["summary"] is None


def test_welfare_kpis_read_persisted_observations(client, registered_animal):
    observed_at = datetime.now(timezone.utc).isoformat()
    response = client.post(
        "/farm/welfare/observations",
        json={
            "animal_id": registered_animal,
            "welfare_domain": "mobility",
            "score": 82.0,
            "status": "OBSERVED",
            "observed_at": observed_at,
            "recorded_by": "Welfare Operator",
        },
    )
    assert response.status_code == 200, response.text

    alert = client.post(
        "/farm/welfare/observations",
        json={
            "animal_id": registered_animal,
            "welfare_domain": "comfort",
            "score": 42.0,
            "status": "ALERT",
            "observed_at": observed_at,
            "recorded_by": "Welfare Operator",
        },
    )
    assert alert.status_code == 200, alert.text

    overview = client.get("/farm/welfare/overview?days=30")
    assert overview.status_code == 200, overview.text
    body = overview.json()
    assert body["data_status"] == "LIVE_PERSISTED_DATA"
    assert body["observation_count"] == 2
    assert body["animals_observed"] == 1
    assert body["summary"]["average_score"] == 62.0
    assert body["summary"]["minimum_score"] == 42.0
    assert body["summary"]["welfare_alert_count"] == 1
    assert body["summary"]["welfare_alert_rate_percent"] == 50.0
    assert body["summary"]["domain_observation_counts"] == {"MOBILITY": 1, "COMFORT": 1}


def test_welfare_observations_survive_repository_reload(client, registered_animal):
    response = client.post(
        "/farm/welfare/observations",
        json={
            "animal_id": registered_animal,
            "welfare_domain": "general",
            "score": 91.0,
            "status": "OBSERVED",
            "recorded_by": "Welfare Operator",
        },
    )
    assert response.status_code == 200, response.text

    factory = RepositoryFactory.create()
    try:
        model = factory.session.query(OperationalStateModel).filter(
            OperationalStateModel.farm_id == "DEFAULT"
        ).first()
        assert model is not None
        observations = list((model.state_payload or {}).get("animal_welfare_observations", []))
        assert any(item.get("animal_id") == registered_animal and item.get("score") == 91.0 for item in observations)
    finally:
        factory.close()

    overview = client.get("/farm/welfare?days=30")
    assert overview.status_code == 200, overview.text
    assert overview.json()["observation_count"] >= 1
