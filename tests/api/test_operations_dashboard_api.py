from dairyos.api.app import app


def test_operations_dashboard(client):

    response = client.get(
        "/operations/dashboard"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["health"] == "GREEN"
    assert body["open_issues"] == 0
    assert body["resolution_rate"] == 100.0
    assert body["effectiveness_score"] == 100.0
