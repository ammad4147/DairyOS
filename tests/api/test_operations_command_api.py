from dairyos.api.app import app


def test_command_status_endpoint(client):

    response = client.get(
        "/operations/commands/status"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["health_status"] == "GREEN"
    assert body["active_attention_count"] == 0
    assert body["has_critical_attention"] is False
