from dairyos.api.app import app


def test_operations_executive_endpoint(client):

    response = client.get(
        "/operations/executive"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["health_status"] in [
        "GREEN",
        "AMBER",
        "RED",
    ]

    assert "attention_count" in body
    assert "critical_issue_count" in body
    assert "owner_action_required" in body
    assert "recommended_focus" in body
    assert "operational_priority_score" in body
