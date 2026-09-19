from __future__ import annotations

from fastapi.testclient import TestClient

from dairyos.api import settings as settings_api
from dairyos.api.auth import get_current_user
from dairyos.auth.permissions import permissions_for_role
from dairyos.app import app


def _admin_override():
    return {"sub": "ADMIN", "role": "ADMIN"}


def test_data_management_export_uses_governed_authority(monkeypatch):
    monkeypatch.setattr(
        settings_api,
        "export_farm_data",
        lambda database_url, path: {
            "path": path,
            "farm_instance_id": "farm-1",
        },
    )

    client = TestClient(app)
    response = client.post(
        "/settings/data-management/export",
        json={"path": "C:/Farm.dairypkg"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["farm_instance_id"] == "farm-1"


def test_data_management_export_does_not_require_bearer_authentication(
    monkeypatch,
):
    """Desktop-session authorization is sufficient for non-destructive export."""
    called = False

    def _export(database_url, path):
        nonlocal called
        called = True
        return {
            "path": path,
            "farm_instance_id": "farm-desktop",
        }

    monkeypatch.setattr(settings_api, "export_farm_data", _export)

    client = TestClient(app)
    response = client.post(
        "/settings/data-management/export",
        json={"path": "C:/Desktop-Farm.dairypkg"},
    )

    assert response.status_code == 200, response.text
    assert called is True
    assert response.json()["farm_instance_id"] == "farm-desktop"


def test_data_management_export_ignores_legacy_user_permission_requirement(
    monkeypatch,
):
    """Export must not inherit the legacy settings.data_management bearer gate."""
    called = False

    def _export(database_url, path):
        nonlocal called
        called = True
        return {
            "path": path,
            "farm_instance_id": "farm-operator",
        }

    monkeypatch.setattr(settings_api, "export_farm_data", _export)

    # Deliberately do not install a get_current_user dependency override.
    # The endpoint must not depend on the legacy bearer-user authority.
    client = TestClient(app)
    response = client.post(
        "/settings/data-management/export",
        json={"path": "C:/Operator-Farm.dairypkg"},
    )

    assert response.status_code == 200, response.text
    assert called is True


def test_data_management_import_requires_exact_confirmation(monkeypatch):
    monkeypatch.setattr(
        settings_api,
        "import_farm_data",
        lambda database_url, path: {"imported": True},
    )
    app.dependency_overrides[get_current_user] = _admin_override
    try:
        client = TestClient(app)
        response = client.post(
            "/settings/data-management/import",
            json={
                "path": "C:/Farm.dairypkg",
                "confirm": "IMPORT",
            },
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_data_management_permission_remains_defined_for_protected_operations():
    """Do not silently remove the permission used by protected data operations."""
    owner_permissions = permissions_for_role("OWNER")
    manager_permissions = permissions_for_role("MANAGER")

    assert "settings.data_management" in owner_permissions
    assert "settings.navigation" in owner_permissions
    assert "settings.data_management" not in manager_permissions
    assert "settings.navigation" not in manager_permissions
