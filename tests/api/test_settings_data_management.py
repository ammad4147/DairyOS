from __future__ import annotations

from fastapi.testclient import TestClient

from dairyos.api import settings as settings_api
from dairyos.api.auth import get_current_user
from dairyos.app import app
from dairyos.auth.permissions import permissions_for_role


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


def test_data_management_export_validate_import_share_desktop_session_boundary(
    monkeypatch,
):
    """The packaged desktop round trip remains available inside protected Settings."""
    calls = []
    monkeypatch.setattr(
        settings_api,
        "export_farm_data",
        lambda database_url, path: calls.append(("export", path)) or {"path": path},
    )
    monkeypatch.setattr(
        settings_api,
        "validate_package",
        lambda path: calls.append(("validate", path)) or {"valid": True},
    )
    monkeypatch.setattr(
        settings_api,
        "import_farm_data",
        lambda database_url, path: calls.append(("import", path)) or {"imported": True},
    )

    client = TestClient(app)
    package = "C:/Desktop-Farm.dairypkg"
    export = client.post("/settings/data-management/export", json={"path": package})
    validate = client.post("/settings/data-management/validate", json={"path": package})
    imported = client.post(
        "/settings/data-management/import",
        json={"path": package, "confirm": "IMPORT VERIFIED FARM DATA"},
    )

    assert [response.status_code for response in (export, validate, imported)] == [200, 200, 200]
    assert calls == [("export", package), ("validate", package), ("import", package)]


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


def test_data_management_routes_require_data_management_permission_on_the_server():
    from dairyos.api.authorization import permission_for_request

    for method, path in (
        ("POST", "/settings/data-management/export"),
        ("POST", "/settings/data-management/validate"),
        ("POST", "/settings/data-management/import"),
        ("GET", "/settings/data-management/packages"),
        ("POST", "/settings/data-management/packages/export"),
        ("POST", "/settings/data-management/packages/validate"),
        ("POST", "/settings/data-management/packages/import"),
    ):
        assert permission_for_request(method, path) == "settings.data_management"
    assert "settings.data_management" in permissions_for_role("PRIMARY_ADMIN")
    for role in ("MILKER", "MANAGER", "ACCOUNTS_OPERATOR", "CUSTOM"):
        assert "settings.data_management" not in permissions_for_role(role)


def _package_folder(monkeypatch, tmp_path):
    data_root = tmp_path / "ProgramData" / "DairyOS"
    monkeypatch.setattr(settings_api.paths, "data_root", lambda create=True: data_root)
    return data_root / "backups" / "farm-packages"


def test_browser_export_saves_into_the_farm_package_folder(monkeypatch, tmp_path):
    folder = _package_folder(monkeypatch, tmp_path)
    exported = []

    def _export(database_url, path):
        exported.append(path)
        path.mkdir(parents=True)
        (path / "metadata.json").write_text('{"exported_at": "2026-09-27T00:00:00Z"}', encoding="utf-8")
        return {"path": str(path), "farm_instance_id": "farm-1"}

    monkeypatch.setattr(settings_api, "export_farm_data", _export)
    client = TestClient(app)

    response = client.post("/settings/data-management/packages/export")
    assert response.status_code == 200, response.text
    body = response.json()
    assert exported == [folder / body["name"]]
    assert body["name"].startswith("DairyOS-Farm-") and body["name"].endswith(".dairypkg")

    listed = client.get("/settings/data-management/packages").json()
    assert listed["folder"] == str(folder)
    assert listed["packages"] == [{"name": body["name"], "exported_at": "2026-09-27T00:00:00Z"}]


def test_browser_validate_and_import_resolve_names_only_inside_the_folder(monkeypatch, tmp_path):
    folder = _package_folder(monkeypatch, tmp_path)
    (folder / "DairyOS-Farm-1.dairypkg").mkdir(parents=True)
    calls = []
    monkeypatch.setattr(
        settings_api, "validate_package",
        lambda path: calls.append(("validate", path)) or {"valid": True},
    )
    monkeypatch.setattr(
        settings_api, "import_farm_data",
        lambda database_url, path: calls.append(("import", path)) or {"imported": True},
    )
    client = TestClient(app)

    ok = client.post("/settings/data-management/packages/validate", json={"name": "DairyOS-Farm-1.dairypkg"})
    assert ok.status_code == 200, ok.text
    wrong_confirm = client.post(
        "/settings/data-management/packages/import",
        json={"name": "DairyOS-Farm-1.dairypkg", "confirm": "IMPORT"},
    )
    assert wrong_confirm.status_code == 422
    imported = client.post(
        "/settings/data-management/packages/import",
        json={"name": "DairyOS-Farm-1.dairypkg", "confirm": "IMPORT VERIFIED FARM DATA"},
    )
    assert imported.status_code == 200, imported.text
    package = (folder / "DairyOS-Farm-1.dairypkg").resolve()
    assert calls == [("validate", package), ("import", package)]

    for bad in ("../secret.dairypkg", "..\\secret.dairypkg", "C:/Farm.dairypkg", "x/y.dairypkg", "notes.txt", ".hidden.dairypkg"):
        response = client.post("/settings/data-management/packages/validate", json={"name": bad})
        assert response.status_code == 422, bad
    missing = client.post("/settings/data-management/packages/validate", json={"name": "Absent.dairypkg"})
    assert missing.status_code == 404
    assert len(calls) == 2


def test_packaged_browser_mode_blocks_non_admins_from_farm_import(monkeypatch, tmp_path):
    """Run the real production middleware as the LAN browser build does."""
    from types import SimpleNamespace

    import dairyos.app as app_module

    folder = _package_folder(monkeypatch, tmp_path)
    (folder / "DairyOS-Farm-1.dairypkg").mkdir(parents=True)
    imported = []
    monkeypatch.setattr(
        settings_api, "import_farm_data",
        lambda database_url, path: imported.append(path) or {"imported": True},
    )
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    monkeypatch.setenv("DAIRYOS_BROWSER_MODE", "1")
    role = {"value": "MILKER"}
    monkeypatch.setattr(
        app_module,
        "_current_session",
        lambda token: (None, SimpleNamespace(role=role["value"])),
    )
    client = TestClient(app)
    request = {"name": "DairyOS-Farm-1.dairypkg", "confirm": "IMPORT VERIFIED FARM DATA"}
    headers = {"X-DairyOS-Human-Session": "session"}

    for blocked_role in ("MILKER", "MANAGER", "ACCOUNTS_OPERATOR"):
        role["value"] = blocked_role
        for method, path, body in (
            ("post", "/settings/data-management/packages/import", request),
            ("post", "/settings/data-management/import", {"path": "C:/Farm.dairypkg", "confirm": "IMPORT VERIFIED FARM DATA"}),
            ("post", "/settings/data-management/export", {"path": "C:/Farm.dairypkg"}),
            ("get", "/settings/data-management/packages", None),
        ):
            response = getattr(client, method)(path, json=body, headers=headers) if body else getattr(client, method)(path, headers=headers)
            assert response.status_code == 403, (blocked_role, path, response.text)
    assert imported == []

    role["value"] = "PRIMARY_ADMIN"
    allowed = client.post("/settings/data-management/packages/import", json=request, headers=headers)
    assert allowed.status_code == 200, allowed.text
    assert imported == [(folder / "DairyOS-Farm-1.dairypkg").resolve()]
