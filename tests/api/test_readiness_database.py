from fastapi.testclient import TestClient

from dairyos.api.app import app


client = TestClient(app)


def test_database_readiness():

    response = client.get("/readiness")

    assert response.status_code == 200

    body = response.json()

    assert body["system"] == "DairyOS"

    assert body["status"] == "READY"

    assert body["database"] == "READY"
