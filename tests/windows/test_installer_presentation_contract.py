from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ISS = ROOT / "tools" / "windows-desktop" / "DairyOS-Installer.iss"

def _source() -> str:
    return ISS.read_text(encoding="utf-8")

def test_installer_uses_clearer_typography_and_separated_data_choices():
    source = _source()
    assert "WizardForm.Font.Name := 'Segoe UI'" in source
    assert "WizardForm.Font.Size := 10" in source
    assert "Existing DairyOS farm data was detected on this computer." in source
    assert "No existing DairyOS farm data was detected on this computer." in source
    assert "Use existing DairyOS data" in source
    assert "Start a new DairyOS farm" in source
    assert "Restore from a verified DairyOS backup" in source
    assert "IMPORTANT:" in source

def test_uninstall_prompt_has_three_clear_actions_without_changing_safety_model():
    source = _source()
    assert "YES — KEEP DATA AND UNINSTALL" in source
    assert "NO — CREATE VERIFIED BACKUP FIRST" in source
    assert "CANCEL — DO NOT UNINSTALL" in source
    assert "Permanent data deletion is available only through authenticated DairyOS Administration." in source
    assert "StopInstalledDairyOSForUninstall" in source
