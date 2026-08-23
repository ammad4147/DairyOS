import uuid

from fastapi.testclient import TestClient


def _login(client: TestClient, username: str, password: str):
    response = client.post(
        "/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_user(
    client: TestClient,
    owner_token: str,
    role: str,
    password: str,
    prefix: str,
):
    username = f"{prefix}-{uuid.uuid4().hex[:8]}"

    response = client.post(
        "/users",
        headers=_auth(owner_token),
        json={
            "username": username,
            "password": password,
            "role": role,
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()

    assert body["username"] == username
    assert body["role"] == role
    assert body["active"] is True

    return body


def test_owner_can_reset_another_users_password(client: TestClient):
    owner = _login(client, "admin", "dairyos")["access_token"]

    target_password = "Initial-Password-2026!"
    reset_password = "Reset-Password-2026!"

    target = _create_user(
        client,
        owner,
        "MANAGER",
        target_password,
        "reset-target",
    )

    response = client.patch(
        f"/users/{target['username']}/password",
        headers=_auth(owner),
        json={"password": reset_password},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["username"] == target["username"]
    assert body["password_reset"] is True

    old_login = client.post(
        "/login",
        json={
            "username": target["username"],
            "password": target_password,
        },
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/login",
        json={
            "username": target["username"],
            "password": reset_password,
        },
    )
    assert new_login.status_code == 200, new_login.text
    assert new_login.json()["user"]["role"] == "MANAGER"


def test_manager_cannot_reset_password(client: TestClient):
    owner = _login(client, "admin", "dairyos")["access_token"]

    manager_password = "Manager-Password-2026!"
    target_password = "Target-Password-2026!"

    manager = _create_user(
        client,
        owner,
        "MANAGER",
        manager_password,
        "reset-manager",
    )

    target = _create_user(
        client,
        owner,
        "MILKER",
        target_password,
        "reset-manager-target",
    )

    manager_token = _login(
        client,
        manager["username"],
        manager_password,
    )["access_token"]

    response = client.patch(
        f"/users/{target['username']}/password",
        headers=_auth(manager_token),
        json={"password": "New-Password-2026!"},
    )

    assert response.status_code == 403, response.text


def test_milker_cannot_reset_password(client: TestClient):
    owner = _login(client, "admin", "dairyos")["access_token"]

    milker_password = "Milker-Password-2026!"
    target_password = "Target-Password-2026!"

    milker = _create_user(
        client,
        owner,
        "MILKER",
        milker_password,
        "reset-milker",
    )

    target = _create_user(
        client,
        owner,
        "MANAGER",
        target_password,
        "reset-milker-target",
    )

    milker_token = _login(
        client,
        milker["username"],
        milker_password,
    )["access_token"]

    response = client.patch(
        f"/users/{target['username']}/password",
        headers=_auth(milker_token),
        json={"password": "New-Password-2026!"},
    )

    assert response.status_code == 403, response.text


def test_user_can_change_own_password(client: TestClient):
    owner = _login(client, "admin", "dairyos")["access_token"]

    current_password = "Current-Password-2026!"
    new_password = "Changed-Password-2026!"

    user = _create_user(
        client,
        owner,
        "MANAGER",
        current_password,
        "self-change",
    )

    token = _login(
        client,
        user["username"],
        current_password,
    )["access_token"]

    response = client.post(
        "/me/password",
        headers=_auth(token),
        json={
            "current_password": current_password,
            "new_password": new_password,
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["password_changed"] is True

    old_login = client.post(
        "/login",
        json={
            "username": user["username"],
            "password": current_password,
        },
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/login",
        json={
            "username": user["username"],
            "password": new_password,
        },
    )
    assert new_login.status_code == 200, new_login.text


def test_self_password_change_rejects_wrong_current_password(
    client: TestClient,
):
    owner = _login(client, "admin", "dairyos")["access_token"]

    current_password = "Correct-Password-2026!"

    user = _create_user(
        client,
        owner,
        "MANAGER",
        current_password,
        "self-invalid",
    )

    token = _login(
        client,
        user["username"],
        current_password,
    )["access_token"]

    response = client.post(
        "/me/password",
        headers=_auth(token),
        json={
            "current_password": "Wrong-Password-2026!",
            "new_password": "Changed-Password-2026!",
        },
    )

    assert response.status_code == 401, response.text
