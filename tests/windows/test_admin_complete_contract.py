from pathlib import Path

from fastapi.testclient import TestClient

from dairyos.admin import app as admin_app


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "src" / "dairyos" / "admin" / "app.py"
CLI = ROOT / "src" / "dairyos" / "admin" / "cli.py"
ISS = ROOT / "tools" / "windows-desktop" / "DairyOS-Installer.iss"


def test_admin_gui_requires_auth_and_exposes_complete_recovery_surface():
    source = APP.read_text(encoding="utf-8")

    for route in (
        '"/setup"',
        '"/login"',
        '"/recover"',
        '"/change-password"',
        '"/restore"',
        '"/rollback"',
        '"/reset"',
        '"/purge"',
        '"/uninstall"',
    ):
        assert route in source
    assert "auth.require_password" in source
    assert "SESSION_TTL_SECONDS" in source
    assert "loopback hosts" in source
    assert '"--no-browser"' in source
    assert "_open_browser_when_ready" in source
    assert "webbrowser.open" in source


def test_admin_cli_has_password_and_recovery_lifecycle():
    source = CLI.read_text(encoding="utf-8")

    for command in ("setup", "recover", "change-password", "restore", "rollback"):
        assert f'sub.add_parser("{command}")' in source
    assert "getpass" in source
    assert "DAIRYOS_ADMIN_PASSWORD" in source


def test_admin_windows_ci_certifies_real_frozen_http_runtime():
    workflow = (ROOT / ".github" / "workflows" / "admin-windows.yml").read_text(
        encoding="utf-8"
    )

    assert "Verify frozen Admin Tool serves the Administration page" in workflow
    assert '"--no-browser","--host","127.0.0.1","--port","18082"' in workflow
    assert "Invoke-WebRequest" in workflow
    assert "http://127.0.0.1:18082/" in workflow
    assert "DairyOS Administration" in workflow


def test_admin_app_really_constructs_and_serves_root(monkeypatch, tmp_path):
    monkeypatch.setenv("DAIRYOS_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(admin_app.auth, "configured", lambda: False)

    application = admin_app.create_app()
    with TestClient(application) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "DairyOS Administration" in response.text
    assert "First-run Administrator Setup" in response.text
