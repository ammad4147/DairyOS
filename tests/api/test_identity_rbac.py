"""Minimal user/RBAC model (D3, 2026-08-14).

Before this, DairyOS had exactly one authenticatable identity: a single
env-var-configured admin login. Five dead "identity"/RBAC trees existed
alongside it, fully wired into the application runtime, but with zero live
callers anywhere in `api/`. This deletes all five and adds one real,
persisted multi-user model instead -- additive to (not replacing) the
legacy env-var admin login, whose exact contract (see test_auth.py,
test_authenticated_operator_attribution.py, test_ui_auth.py,
test_farm_data_entry_auth.py) must keep passing unchanged.
"""

from fastapi.testclient import TestClient

from dairyos.api.reference_data import GOVERNED


def _login(client, username, password):
    return client.post("/login", json={"username": username, "password": password})


def _owner_token(client, monkeypatch):
    monkeypatch.setenv("DAIRYOS_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("DAIRYOS_ADMIN_PASSWORD", "test-password")
    monkeypatch.setenv("DAIRYOS_ADMIN_ROLE", "OWNER")
    monkeypatch.setenv("DAIRYOS_AUTH_SECRET", "test-secret")
    response = _login(client, "admin", "test-password")
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


# ---------------------------------------------------------------------------
# Governed vocabulary
# ---------------------------------------------------------------------------


def test_auth_roles_are_governed():
    assert GOVERNED["auth_roles"] == ["OWNER", "MANAGER", "MILKER"]


# ---------------------------------------------------------------------------
# OWNER creates and lists persisted users
# ---------------------------------------------------------------------------


def test_owner_can_create_a_user(client: TestClient, monkeypatch):
    token = _owner_token(client, monkeypatch)

    response = client.post(
        "/users",
        json={"username": "manager1", "password": "s3cret-pass", "role": "MANAGER"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["username"] == "manager1"
    assert body["role"] == "MANAGER"
    assert body["active"] is True


def test_owner_can_list_created_users(client: TestClient, monkeypatch):
    token = _owner_token(client, monkeypatch)

    client.post(
        "/users",
        json={"username": "milker1", "password": "s3cret-pass", "role": "MILKER"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get("/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.text
    usernames = {u["username"] for u in response.json()["users"]}
    assert "milker1" in usernames


def test_creating_a_user_with_ungoverned_role_is_rejected(client: TestClient, monkeypatch):
    token = _owner_token(client, monkeypatch)

    response = client.post(
        "/users",
        json={"username": "rogue1", "password": "s3cret-pass", "role": "SUPERADMIN"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422, response.text


def test_duplicate_username_is_rejected(client: TestClient, monkeypatch):
    token = _owner_token(client, monkeypatch)

    client.post(
        "/users",
        json={"username": "dup1", "password": "s3cret-pass", "role": "MILKER"},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.post(
        "/users",
        json={"username": "dup1", "password": "another-pass", "role": "MANAGER"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409, response.text


def test_non_owner_cannot_create_users(client: TestClient, monkeypatch):
    monkeypatch.setenv("DAIRYOS_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("DAIRYOS_ADMIN_PASSWORD", "test-password")
    monkeypatch.setenv("DAIRYOS_ADMIN_ROLE", "MILKER")
    monkeypatch.setenv("DAIRYOS_AUTH_SECRET", "test-secret")

    login_response = _login(client, "admin", "test-password")
    token = login_response.json()["access_token"]

    response = client.post(
        "/users",
        json={"username": "sneaky", "password": "s3cret-pass", "role": "OWNER"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403, response.text


def test_users_endpoint_requires_authentication(client: TestClient):
    response = client.get("/users")
    assert response.status_code == 401, response.text


# ---------------------------------------------------------------------------
# A persisted user can log in with their own credentials
# ---------------------------------------------------------------------------


def test_persisted_user_can_log_in_with_their_own_password(client: TestClient, monkeypatch):
    token = _owner_token(client, monkeypatch)

    client.post(
        "/users",
        json={"username": "realmanager", "password": "correct-horse", "role": "MANAGER"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = _login(client, "realmanager", "correct-horse")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["user"] == {"username": "realmanager", "role": "MANAGER"}

    me = client.get("/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["role"] == "MANAGER"


def test_persisted_user_login_rejects_wrong_password(client: TestClient, monkeypatch):
    token = _owner_token(client, monkeypatch)

    client.post(
        "/users",
        json={"username": "realmilker", "password": "correct-horse", "role": "MILKER"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = _login(client, "realmilker", "wrong-password")
    assert response.status_code == 401, response.text


# ---------------------------------------------------------------------------
# The legacy env-var admin login must remain reachable when the username
# doesn't match any persisted user -- this is the whole point of the
# additive (not replacing) design.
# ---------------------------------------------------------------------------


def test_legacy_admin_login_still_works_when_no_persisted_user_matches(
    client: TestClient, monkeypatch
):
    monkeypatch.setenv("DAIRYOS_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("DAIRYOS_ADMIN_PASSWORD", "test-password")
    monkeypatch.setenv("DAIRYOS_ADMIN_ROLE", "operator")
    monkeypatch.setenv("DAIRYOS_AUTH_SECRET", "test-secret")

    response = _login(client, "admin", "test-password")
    assert response.status_code == 200, response.text
    assert response.json()["user"] == {"username": "admin", "role": "operator"}


def test_a_persisted_username_matching_the_legacy_admin_takes_priority(
    client: TestClient, monkeypatch
):
    """If a persisted user shares the legacy admin's username, the persisted
    row is authoritative -- the legacy env-var password no longer works for
    that username once it's been claimed by a real account."""

    token = _owner_token(client, monkeypatch)

    client.post(
        "/users",
        json={"username": "admin", "password": "new-real-password", "role": "MANAGER"},
        headers={"Authorization": f"Bearer {token}"},
    )

    legacy_attempt = _login(client, "admin", "test-password")
    assert legacy_attempt.status_code == 401, legacy_attempt.text

    real_attempt = _login(client, "admin", "new-real-password")
    assert real_attempt.status_code == 200, real_attempt.text
    assert real_attempt.json()["user"]["role"] == "MANAGER"
