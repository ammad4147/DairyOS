from fastapi.testclient import TestClient

from dairyos.api.app import app


client = TestClient(app)


def test_version_endpoint():

    response = client.get("/version")

    assert response.status_code == 200

    body = response.json()

    assert body["system"] == "DairyOS"
    assert body["version"] == "0.10.0"
    assert body["api"] == "Enterprise API"
