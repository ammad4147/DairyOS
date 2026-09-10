from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ISS = ROOT / "tools" / "windows-desktop" / "DairyOS-Installer.iss"
BUILD = ROOT / "scripts" / "Build-DairyOS-Installer.ps1"
SETTINGS = ROOT / "src/DairyOS.Web/src/components/SettingsTab.tsx"
SPEC = ROOT / "DairyOS.spec"


def test_standalone_administration_product_surface_is_retired():
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert not (ROOT / "src/dairyos/admin/app.py").exists()
    assert not (ROOT / "src/dairyos/admin/cli.py").exists()
    assert not (ROOT / "scripts/Build-DairyOS-Admin.ps1").exists()
    assert not (ROOT / "scripts/Start-DairyOS-Admin.ps1").exists()
    assert not (ROOT / "packaging/dairyos_admin.spec").exists()
    assert not (ROOT / ".github/workflows/admin-windows.yml").exists()
    assert not (ROOT / ".github/workflows/admin-postgres.yml").exists()
    assert "dairyos-admin =" not in project
    assert "dairyos-admin-cli =" not in project


def test_protected_settings_replaces_the_operator_facing_admin_surface():
    settings = SETTINGS.read_text(encoding="utf-8-sig")
    assert "Read-only System Health" in settings
    assert "/settings/system-reset" in settings
    assert "DairyOS Assistant" in settings
    assert "TrainingSimulator" not in settings


def test_release_package_excludes_standalone_admin_and_manual():
    iss = ISS.read_text(encoding="utf-8-sig")
    build = BUILD.read_text(encoding="utf-8-sig")
    spec = SPEC.read_text(encoding="utf-8-sig")

    assert "DairyOS-Admin.exe" not in iss
    assert "DairyOS Administration" not in iss
    assert "DairyOS-Operator-Manual.html" not in iss
    assert "DairyOS-Operator-Manual.html" not in build
    assert "dairyos.admin.app" not in spec
    assert "dairyos.admin.cli" not in spec
