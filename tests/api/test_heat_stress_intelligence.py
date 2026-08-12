from datetime import datetime, timezone
from uuid import uuid4


def test_heat_stress_intelligence_reports_no_data_without_observations(client):
    farm_id = f"HEAT-EMPTY-{uuid4().hex}"
    response = client.get(f"/farm/heat-stress/intelligence?farm_id={farm_id}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data_status"] == "NO_ENVIRONMENTAL_OBSERVATION"
    assert body["observation_count"] == 0
    assert body["latest"] is None


def test_heat_stress_intelligence_persists_and_aggregates_observations(client):
    farm_id = f"HEAT-LIVE-{uuid4().hex}"
    timestamps = [
        "2026-08-12T08:00:00+00:00",
        "2026-08-12T10:00:00+00:00",
        "2026-08-12T12:00:00+00:00",
    ]
    observations = [(20.0, 50.0), (30.0, 70.0), (32.0, 75.0)]
    for observed_at, (temperature_c, humidity_pct) in zip(timestamps, observations):
        response = client.post(
            "/farm/heat-stress/intelligence/observations",
            json={
                "farm_id": farm_id,
                "temperature_c": temperature_c,
                "humidity_pct": humidity_pct,
                "observed_at": observed_at,
                "recorded_by": "Operator",
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["data_status"] == "PERSISTED"

    overview = client.get(f"/farm/heat-stress/intelligence?farm_id={farm_id}&days=7")
    assert overview.status_code == 200, overview.text
    body = overview.json()
    assert body["data_status"] == "LIVE_PERSISTED"
    assert body["observation_count"] == 3
    assert body["summary"]["maximum_thi"] >= body["summary"]["average_thi"]
    assert body["summary"]["current_risk"] in {"ALERT", "HIGH", "SEVERE"}
    assert body["summary"]["consecutive_elevated_observations"] == 2
    assert body["summary"]["alert"] is True
    assert body["actions"]
    assert body["latest"]["observed_at"] == timestamps[-1]


def test_heat_stress_intelligence_survives_repository_reload(client):
    farm_id = f"HEAT-RESTART-{uuid4().hex}"
    response = client.post(
        "/farm/heat-stress/intelligence/observations",
        json={
            "farm_id": farm_id,
            "temperature_c": 33.0,
            "humidity_pct": 80.0,
            "observed_at": datetime(2026, 8, 12, 9, tzinfo=timezone.utc).isoformat(),
        },
    )
    assert response.status_code == 200, response.text

    # A new request obtains a fresh RepositoryFactory/session and must read the persisted projection.
    reloaded = client.get(f"/farm/heat-stress/intelligence?farm_id={farm_id}&days=7")
    assert reloaded.status_code == 200, reloaded.text
    body = reloaded.json()
    assert body["data_status"] == "LIVE_PERSISTED"
    assert body["observation_count"] == 1
    assert body["latest"]["temperature_c"] == 33.0
    assert body["latest"]["humidity_pct"] == 80.0
