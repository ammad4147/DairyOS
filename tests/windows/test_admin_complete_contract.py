from pathlib import Path


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


def test_admin_cli_has_password_and_recovery_lifecycle():
    source = CLI.read_text(encoding="utf-8")

    for command in ("setup", "recover", "change-password", "restore", "rollback"):
        assert f'sub.add_parser("{command}")' in source
    assert "getpass" in source
    assert "DAIRYOS_ADMIN_PASSWORD" in source
