from fastapi.testclient import TestClient

from dairyos.api.app import app


client = TestClient(app)


def test_operations_health():

    response = client.get(
        "/operations/health"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["health_status"] == "GREEN"

    assert body["operational_score"] == 100.0

    assert body["owner_attention_required"] is False
