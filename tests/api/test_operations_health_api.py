from dairyos.api.app import app


def test_operations_health():
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.get(
        "/operations/health"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["health_status"] == "AMBER"
    assert body["operational_score"] < 100.0
    assert body["owner_attention_required"] is True
    assert body["runtime"] == "ACTIVE"