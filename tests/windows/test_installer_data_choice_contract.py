from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ISS = ROOT / "tools" / "windows-desktop" / "DairyOS-Installer.iss"


def _source() -> str:
    return ISS.read_text(encoding="utf-8")


def test_installer_exposes_existing_data_and_restore_choices():
    source = _source()

    assert "DetectExistingDairyOSData" in source
    assert "Use existing DairyOS data (recommended)" in source
    assert "Restore a verified backup using DairyOS Administration after installation" in source
    assert "Start a new DairyOS farm" in source
    assert "ShouldLaunchAdminAfterInstall" in source
    assert "The installer itself will not overwrite farm data." in source


def test_uninstaller_explicitly_keeps_data_and_routes_backup_to_admin_tool():
    source = _source()

    assert "DairyOS farm data and the private database are retained by default" in source
    assert "continue uninstall and KEEP all DairyOS data" in source
    assert "create a verified backup first" in source
    assert "DairyOS-Admin.exe" in source
    assert "Permanent data deletion is available only through" in source
