"""Persisted users, customizable access presets, and admin credential controls."""

from fastapi.testclient import TestClient

from dairyos.api.reference_data import GOVERNED


def _login(client, username, password):
    return client.post("/login", json={"username": username, "password": password})


def _admin_token(client, monkeypatch):
    monkeypatch.setenv("DAIRYOS_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("DAIRYOS_ADMIN_PASSWORD", "test-password")
    monkeypatch.setenv("DAIRYOS_ADMIN_ROLE", "OWNER")  # Must be ignored: bootstrap identity is always ADMIN.
    monkeypatch.setenv("DAIRYOS_AUTH_SECRET", "test-secret")
    response = _login(client, "admin", "test-password")
    assert response.status_code == 200, response.text
    assert response.json()["user"] == {"username": "admin", "role": "ADMIN"}
    return response.json()["access_token"]


def test_auth_roles_include_admin_and_custom_access_preset():
    assert GOVERNED["auth_roles"] == ["ADMIN", "OWNER", "MANAGER", "MILKER", "CUSTOM"]


def test_bootstrap_admin_role_cannot_be_changed_by_environment(client: TestClient, monkeypatch):
    monkeypatch.setenv("DAIRYOS_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("DAIRYOS_ADMIN_PASSWORD", "test-password")
    monkeypatch.setenv("DAIRYOS_ADMIN_ROLE", "OWNER")
    monkeypatch.setenv("DAIRYOS_AUTH_SECRET", "test-secret")
    response = _login(client, "admin", "test-password")
    assert response.status_code == 200, response.text
    assert response.json()["user"] == {"username": "admin", "role": "ADMIN"}
    me = client.get("/me", headers={"Authorization": f"Bearer {response.json()['access_token']}"})
    assert me.status_code == 200
    assert me.json()["role"] == "ADMIN"


def test_admin_can_create_a_custom_user(client: TestClient, monkeypatch):
    token = _admin_token(client, monkeypatch)
    response = client.post(
        "/users",
        json={"username": "custom1", "password": "s3cret-pass", "role": "CUSTOM"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["role"] == "CUSTOM"


def test_admin_can_create_a_user(client: TestClient, monkeypatch):
    token = _admin_token(client, monkeypatch)
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


def test_admin_can_list_created_users(client: TestClient, monkeypatch):
    token = _admin_token(client, monkeypatch)
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
    token = _admin_token(client, monkeypatch)
    response = client.post(
        "/users",
        json={"username": "rogue1", "password": "s3cret-pass", "role": "SUPERADMIN"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422, response.text


def test_duplicate_username_is_rejected(client: TestClient, monkeypatch):
    token = _admin_token(client, monkeypatch)
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


def test_non_admin_cannot_create_users(client: TestClient, monkeypatch):
    admin_token = _admin_token(client, monkeypatch)
    created = client.post(
        "/users",
        json={"username": "milker-no-admin", "password": "s3cret-pass", "role": "MILKER"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert created.status_code == 200, created.text

    login_response = _login(client, "milker-no-admin", "s3cret-pass")
    assert login_response.status_code == 200, login_response.text
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


def test_persisted_user_can_log_in_with_their_own_password(client: TestClient, monkeypatch):
    token = _admin_token(client, monkeypatch)
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
    token = _admin_token(client, monkeypatch)
    client.post(
        "/users",
        json={"username": "realmilker", "password": "correct-horse", "role": "MILKER"},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = _login(client, "realmilker", "wrong-password")
    assert response.status_code == 401, response.text


def test_legacy_admin_password_can_be_changed(client: TestClient, monkeypatch):
    monkeypatch.setenv("DAIRYOS_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("DAIRYOS_ADMIN_PASSWORD", "test-password")
    monkeypatch.setenv("DAIRYOS_ADMIN_ROLE", "OWNER")
    monkeypatch.setenv("DAIRYOS_AUTH_SECRET", "test-secret")

    login_response = _login(client, "admin", "test-password")
    assert login_response.status_code == 200, login_response.text
    assert login_response.json()["user"]["role"] == "ADMIN"
    token = login_response.json()["access_token"]

    changed = client.post(
        "/me/password",
        json={"current_password": "test-password", "new_password": "new-admin-password"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert changed.status_code == 200, changed.text

    assert _login(client, "admin", "test-password").status_code == 401
    assert _login(client, "admin", "new-admin-password").status_code == 200


def test_legacy_admin_password_change_rejects_wrong_current_password(client: TestClient, monkeypatch):
    monkeypatch.setenv("DAIRYOS_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("DAIRYOS_ADMIN_PASSWORD", "test-password")
    monkeypatch.setenv("DAIRYOS_ADMIN_ROLE", "OWNER")
    monkeypatch.setenv("DAIRYOS_AUTH_SECRET", "test-secret")
    login_response = _login(client, "admin", "test-password")
    token = login_response.json()["access_token"]

    response = client.post(
        "/me/password",
        json={"current_password": "wrong-password", "new_password": "new-admin-password"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401, response.text


def test_legacy_admin_login_is_always_admin_when_no_persisted_user_matches(client: TestClient, monkeypatch):
    monkeypatch.setenv("DAIRYOS_ADMIN_USERNAME", "legacy-admin")
    monkeypatch.setenv("DAIRYOS_ADMIN_PASSWORD", "test-password")
    monkeypatch.setenv("DAIRYOS_ADMIN_ROLE", "operator")
    monkeypatch.setenv("DAIRYOS_AUTH_SECRET", "test-secret")
    response = _login(client, "legacy-admin", "test-password")
    assert response.status_code == 200, response.text
    assert response.json()["user"] == {"username": "legacy-admin", "role": "ADMIN"}
