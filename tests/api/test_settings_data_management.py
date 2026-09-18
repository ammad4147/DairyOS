from __future__ import annotations

from fastapi.testclient import TestClient

from dairyos.api import settings as settings_api
from dairyos.api.auth import get_current_user
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
