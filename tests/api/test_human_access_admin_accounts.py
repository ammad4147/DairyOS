"""Administrator identity lifecycle tests use the disposable API test database."""

import pytest

from dairyos.data.models.human_identity import HumanIdentity, HumanSession
from dairyos.data.repositories.repository_factory import RepositoryFactory


def _clear_human_access_rows():
    factory = RepositoryFactory.create()
    try:
        factory.session.query(HumanSession).delete(synchronize_session=False)
        factory.session.query(HumanIdentity).delete(synchronize_session=False)
        factory.session.commit()
    finally:
        factory.close()


@pytest.fixture(autouse=True)
def isolate_human_access_rows():
    _clear_human_access_rows()
    yield
    _clear_human_access_rows()


def _bootstrap_admin(client):
    response = client.post(
        "/human-access/bootstrap",
        json={"display_name": "Lifecycle Test Admin", "pin": "4826", "pin_confirmation": "4826"},
    )
    assert response.status_code == 200, response.text
    identity_id = response.json()["id"]
    login = client.post("/human-access/login", json={"identity_id": identity_id, "pin": "4826"})
    assert login.status_code == 200, login.text
    return identity_id, login.json()["session_token"]


def test_management_roster_requires_admin_and_includes_inactive_accounts(client):
    admin_id, admin_token = _bootstrap_admin(client)
    headers = {"X-DairyOS-Human-Session": admin_token}
    created = client.post(
        "/human-access/people",
        headers=headers,
        json={"display_name": "Inactive Test Operator", "entry_group": "MILK_OPERATOR"},
    )
    assert created.status_code == 200, created.text
    operator_id = created.json()["id"]
    deactivated = client.patch(
        f"/human-access/people/{operator_id}/active?active=false", headers=headers
    )
    assert deactivated.status_code == 200, deactivated.text

    assert client.get("/human-access/people/manage").status_code == 401
    response = client.get("/human-access/people/manage", headers=headers)
    assert response.status_code == 200, response.text
    roster = {person["id"]: person for person in response.json()["people"]}
    assert roster[operator_id]["active"] is False
    assert roster[admin_id]["role"] == "PRIMARY_ADMIN"


def test_admin_can_delete_operator_identity_and_revoke_its_sessions_but_keep_other_users(client):
    _admin_id, admin_token = _bootstrap_admin(client)
    admin_headers = {"X-DairyOS-Human-Session": admin_token}
    created = client.post(
        "/human-access/people",
        headers=admin_headers,
        json={"display_name": "Delete Lifecycle Operator", "entry_group": "MILK_OPERATOR"},
    )
    assert created.status_code == 200, created.text
    operator_id = created.json()["id"]
    initialized = client.post(
        f"/human-access/people/{operator_id}/pin/initial",
        headers=admin_headers,
        json={"pin": "6382", "pin_confirmation": "6382"},
    )
    assert initialized.status_code == 200, initialized.text
    operator_login = client.post(
        "/human-access/login", json={"identity_id": operator_id, "pin": "6382"}
    )
    assert operator_login.status_code == 200, operator_login.text
    operator_headers = {"X-DairyOS-Human-Session": operator_login.json()["session_token"]}

    deleted = client.delete(f"/human-access/people/{operator_id}", headers=admin_headers)
    assert deleted.status_code == 200, deleted.text
    assert deleted.json() == {"deleted": True, "identity_id": operator_id}
    assert client.get("/human-access/me", headers=operator_headers).status_code == 401
    roster = client.get("/human-access/people/manage", headers=admin_headers)
    assert roster.status_code == 200, roster.text
    assert {person["id"] for person in roster.json()["people"]} == {_admin_id}
    assert client.get("/human-access/me", headers=admin_headers).status_code == 200


def test_admin_cannot_delete_own_primary_account(client):
    admin_id, admin_token = _bootstrap_admin(client)
    response = client.delete(
        f"/human-access/people/{admin_id}",
        headers={"X-DairyOS-Human-Session": admin_token},
    )
    assert response.status_code == 409
    assert "cannot delete their own" in response.json()["detail"]


def test_operator_cannot_view_management_roster_or_delete_accounts(client):
    _admin_id, admin_token = _bootstrap_admin(client)
    admin_headers = {"X-DairyOS-Human-Session": admin_token}
    created = client.post(
        "/human-access/people",
        headers=admin_headers,
        json={"display_name": "Restricted Test Operator", "entry_group": "MILK_OPERATOR"},
    )
    assert created.status_code == 200, created.text
    operator_id = created.json()["id"]
    initialized = client.post(
        f"/human-access/people/{operator_id}/pin/initial",
        headers=admin_headers,
        json={"pin": "6382", "pin_confirmation": "6382"},
    )
    assert initialized.status_code == 200, initialized.text
    login = client.post(
        "/human-access/login", json={"identity_id": operator_id, "pin": "6382"}
    )
    assert login.status_code == 200, login.text
    operator_headers = {"X-DairyOS-Human-Session": login.json()["session_token"]}

    assert client.get("/human-access/people/manage", headers=operator_headers).status_code == 403
    assert client.delete(
        f"/human-access/people/{_admin_id}", headers=operator_headers
    ).status_code == 403
