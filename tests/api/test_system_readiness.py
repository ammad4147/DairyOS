from fastapi.testclient import TestClient

import dairyos.api.system as system_api



def test_readiness_reports_live_database_and_runtime(client: TestClient):
    response = client.get("/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "READY"
    assert payload["database"] == "READY"
    assert payload["runtime"] == "ACTIVE"
    assert isinstance(payload["events"], int)



def test_readiness_rejects_database_failure(client: TestClient, monkeypatch):
    class BrokenConnection:
        def __enter__(self):
            raise RuntimeError("database unavailable")

        def __exit__(self, exc_type, exc_value, traceback):
            return False

    class BrokenEngine:
        def connect(self):
            return BrokenConnection()

    monkeypatch.setattr(system_api, "engine", BrokenEngine())

    response = client.get("/readiness")

    assert response.status_code == 503
    payload = response.json()["detail"]
    assert payload["status"] == "NOT_READY"
    assert payload["database"] == "NOT_READY"
    assert payload["runtime"] == "ACTIVE"
