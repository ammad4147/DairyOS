from dairyos.api.app import app


def test_command_center_endpoint(client):

    response = client.get(
        "/command-center"
    )

    assert response.status_code == 200

    body = response.json()

    assert "status" in body
    assert "attention" in body
    assert "decisions" in body
    assert "actions" in body
    assert "confidence" in body

    assert isinstance(
        body["status"],
        dict,
    )

    assert isinstance(
        body["attention"],
        list,
    )

    assert isinstance(
        body["decisions"],
        dict,
    )

    assert isinstance(
        body["actions"],
        list,
    )

    assert isinstance(
        body["confidence"],
        dict,
    )
