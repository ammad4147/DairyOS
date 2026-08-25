from fastapi.testclient import TestClient

from dairyos.auth.permissions import has_permission, permissions_for_role


def login(client: TestClient, monkeypatch, role: str, username: str = "role-user"):
    monkeypatch.setenv("DAIRYOS_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("DAIRYOS_ADMIN_PASSWORD", "test-password")
    monkeypatch.setenv("DAIRYOS_AUTH_SECRET", "test-secret")

    admin_response = client.post("/login", json={"username": "admin", "password": "test-password"})
    assert admin_response.status_code == 200
    admin_token = admin_response.json()["access_token"]

    create_response = client.post(
        "/users",
        json={"username": username, "password": "role-password", "role": role},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_response.status_code in (200, 409), create_response.text

    response = client.post("/login", json={"username": username, "password": "role-password"})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_owner_has_full_permission_matrix():
    permissions = permissions_for_role("OWNER")
    assert "users.view" in permissions
    assert "users.create" in permissions
    assert "finance.void" in permissions
    assert "animals.disposition" in permissions


def test_manager_can_manage_operations_but_not_users_or_void_finance():
    permissions = permissions_for_role("MANAGER")
    assert has_permission("MANAGER", "milk.create")
    assert has_permission("MANAGER", "finance.create_feed")
    assert has_permission("MANAGER", "finance.create_opex")
    assert has_permission("MANAGER", "finance.edit")
    assert not has_permission("MANAGER", "finance.void")
    assert not has_permission("MANAGER", "users.view")


def test_milker_is_operationally_limited():
    assert has_permission("MILKER", "milk.create")
    assert has_permission("MILKER", "feed.create")
    assert has_permission("MILKER", "animals.view")
    assert not has_permission("MILKER", "finance.view")
    assert not has_permission("MILKER", "users.view")


def test_permissions_endpoint_returns_effective_role_permissions(client: TestClient, monkeypatch):
    token = login(client, monkeypatch, "MANAGER", "manager-permissions")
    response = client.get("/authz/permissions", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["role"] == "MANAGER"
    assert "finance.create_feed" in payload["permissions"]


def test_permission_matrix_is_owner_only(client: TestClient, monkeypatch):
    token = login(client, monkeypatch, "MANAGER", "manager-matrix")
    response = client.get("/authz/matrix", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_milker_cannot_access_finance_api(client: TestClient, monkeypatch):
    token = login(client, monkeypatch, "MILKER", "milker-finance-read")
    response = client.get("/farm/finance-ledger", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_milker_cannot_create_finance_expense(client: TestClient, monkeypatch):
    token = login(client, monkeypatch, "MILKER", "milker-finance-write")
    response = client.post(
        "/farm/finance-ledger",
        headers={"Authorization": f"Bearer {token}"},
        json={"transaction_type": "EXPENSE", "master_category": "FEED", "sub_category": "Corn / Maize Silage", "amount": 1000},
    )
    assert response.status_code == 403
