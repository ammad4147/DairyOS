from __future__ import annotations

from fastapi.testclient import TestClient

from dairyos.api import settings as settings_api
from dairyos.api.auth import get_current_user
from dairyos.auth.permissions import permissions_for_role
from dairyos.app import app


def _admin_override():
    return {"sub": "ADMIN", "role": "ADMIN"}


def test_data_management_export_uses_governed_authority(monkeypatch):
    monkeypatch.setattr(settings_api, "export_farm_data", lambda database_url, path: {"path": path, "farm_instance_id": "farm-1"})
    app.dependency_overrides[get_current_user] = _admin_override
    try:
        client = TestClient(app)
        response = client.post("/settings/data-management/export", json={"path": "C:/Farm.dairypkg"})
        assert response.status_code == 200
        assert response.json()["farm_instance_id"] == "farm-1"
    finally:
        app.dependency_overrides.clear()


def test_data_management_import_requires_exact_confirmation(monkeypatch):
    monkeypatch.setattr(settings_api, "import_farm_data", lambda database_url, path: {"imported": True})
    app.dependency_overrides[get_current_user] = _admin_override
    try:
        client = TestClient(app)
        response = client.post("/settings/data-management/import", json={"path": "C:/Farm.dairypkg", "confirm": "IMPORT"})
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def _owner_override():
    return {"sub": "DATA-MANAGEMENT-OWNER", "role": "OWNER"}


def _manager_override():
    return {"sub": "DATA-MANAGEMENT-MANAGER", "role": "MANAGER"}


def test_data_management_has_dedicated_permission_separate_from_navigation():
    owner_permissions = permissions_for_role("OWNER")
    manager_permissions = permissions_for_role("MANAGER")
    assert "settings.data_management" in owner_permissions
    assert "settings.navigation" in owner_permissions
    assert "settings.data_management" not in manager_permissions
    assert "settings.navigation" not in manager_permissions


def test_data_management_export_accepts_normal_owner_session(monkeypatch):
    monkeypatch.setattr(
        settings_api,
        "export_farm_data",
        lambda database_url, path: {"path": path, "farm_instance_id": "farm-owner"},
    )
    app.dependency_overrides[get_current_user] = _owner_override
    try:
        client = TestClient(app)
        response = client.post(
            "/settings/data-management/export",
            json={"path": "C:/Owner-Farm.dairypkg"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["farm_instance_id"] == "farm-owner"
    finally:
        app.dependency_overrides.clear()


def test_data_management_rejects_session_without_data_management_permission(monkeypatch):
    called = False

    def _export(database_url, path):
        nonlocal called
        called = True
        return {"path": path}

    monkeypatch.setattr(settings_api, "export_farm_data", _export)
    app.dependency_overrides[get_current_user] = _manager_override
    try:
        client = TestClient(app)
        response = client.post(
            "/settings/data-management/export",
            json={"path": "C:/Denied.dairypkg"},
        )
        assert response.status_code == 403, response.text
        assert response.json()["detail"] == "Permission required: settings.data_management"
        assert called is False
    finally:
        app.dependency_overrides.clear()
