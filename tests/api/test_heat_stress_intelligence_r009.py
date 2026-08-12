from datetime import datetime, timezone

from fastapi.testclient import TestClient

from dairyos.app import app


def test_heat_stress_observation_persists_and_intelligence_reads_it():
    with TestClient(app) as client:
        observed_at = datetime.now(timezone.utc).isoformat()
        response = client.post(
            "/farm/heat-stress/intelligence/observations",
            json={
                "temperature_c": 35.0,
                "humidity_pct": 70.0,
                "observed_at": observed_at,
                "recorded_by": "R009-TEST",
                "farm_id": "R009-TEST-FARM",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["data_status"] == "PERSISTED"
        assert body["temperature_c"] == 35.0
        assert body["humidity_pct"] == 70.0
        assert body["thi"] > 72
        assert body["risk"] in {"HIGH", "SEVERE"}

        intelligence = client.get(
            "/farm/heat-stress/intelligence",
            params={"farm_id": "R009-TEST-FARM", "days": 7},
        )
        assert intelligence.status_code == 200
        result = intelligence.json()
        assert result["data_status"] == "LIVE_PERSISTED"
        assert result["observation_count"] >= 1
        assert result["latest"]["recorded_by"] == "R009-TEST"
        assert result["summary"]["maximum_thi"] == body["thi"]
        assert result["summary"]["current_risk"] == body["risk"]
        assert result["summary"]["alert"] is True
        assert result["actions"]


def test_heat_stress_intelligence_does_not_invent_data():
    with TestClient(app) as client:
        response = client.get(
            "/farm/heat-stress/intelligence",
            params={"farm_id": "R009-NO-DATA", "days": 7},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["data_status"] == "NO_ENVIRONMENTAL_OBSERVATION"
        assert result["observation_count"] == 0
        assert result["latest"] is None
        assert result["summary"] is None
        assert result["actions"] == []


def test_heat_stress_observation_rejects_invalid_environmental_inputs():
    with TestClient(app) as client:
        temperature = client.post(
            "/farm/heat-stress/intelligence/observations",
            json={"temperature_c": 61, "humidity_pct": 70, "farm_id": "R009-INVALID"},
        )
        assert temperature.status_code == 422

        humidity = client.post(
            "/farm/heat-stress/intelligence/observations",
            json={"temperature_c": 35, "humidity_pct": 101, "farm_id": "R009-INVALID"},
        )
        assert humidity.status_code == 422
