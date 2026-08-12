from fastapi.testclient import TestClient

from dairyos.api.auth import _operator
from dairyos.app import app


client = TestClient(app)


def test_farm_write_requires_authenticated_operator():
    response = client.post(
        "/farm/workforce",
        json={
            "worker_id": "W-001",
            "activity": "MILKING",
            "operator": "forged-operator",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_authenticated_claim_overrides_client_operator_identity():
    operator = _operator(
        {"operator": "forged-operator"},
        {"sub": "authenticated-operator", "role": "admin"},
    )

    assert operator == "authenticated-operator"
    assert operator != "forged-operator"


def test_login_issues_identity_bearing_token():
    response = client.post(
        "/login",
        json={"username": "admin", "password": "dairyos"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["username"] == "admin"
    assert body["user"]["role"] == "admin"
    assert body["access_token"]
