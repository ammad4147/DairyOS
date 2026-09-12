from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ISS = ROOT / "tools" / "windows-desktop" / "DairyOS-Installer.iss"

def _source() -> str:
    return ISS.read_text(encoding="utf-8")

def test_installer_uses_large_dpi_aware_data_choice_page():
    source = _source()

    assert "VersionInfoComments=" not in source
    assert "WizardResizable=" not in source
    assert "WizardSizePercent=140,135" in source
    assert "ScaleX(" in source
    assert "ScaleY(" in source
    assert ".AdjustHeight();" in source
    assert "Existing DairyOS farm data was detected on this computer." in source
    assert "No existing DairyOS farm data was detected on this computer." in source
    assert "INSTALLER STATUS: the existing farm database and ProgramData records will be retained." in source
    assert "INSTALLER STATUS: no existing farm data was detected." in source
    assert "This page is informational, not a data-choice control." in source
    assert "Restore from a verified DairyOS backup" not in source
    assert "The installer will not delete or overwrite an existing DairyOS farm database." in source
    assert "A protected zero-state reset is available from Settings after the application starts." in source
    assert "WizardForm.Font.Name" not in source
    assert "WizardForm.Font.Size" not in source


def test_install_data_choice_does_not_use_small_followup_message_boxes():
    source = _source()
    start = source.index("function NextButtonClick")
    end = source.index("function ShouldLaunchDairyOS", start)
    block = source[start:end]

    assert "MsgBox(" not in block
    assert "RestoreRequested" not in block

def test_uninstall_prompt_keeps_data_without_standalone_admin():
    source = _source()
    assert "YES - PRESERVE FARM DATA AND UNINSTALL" in source
    assert "NO - CANCEL AND KEEP THE APPLICATION" in source
    assert "CANCEL - DO NOT UNINSTALL" not in source
    assert "DairyOS Administration" not in source
    assert "DairyOS-Admin.exe" not in source
    assert "StopInstalledDairyOSForUninstall" in source


def test_installer_user_facing_text_avoids_garbled_unicode_punctuation():
    source = _source()

    assert "•" not in source
    assert "—" not in source
    assert "YES - PRESERVE FARM DATA AND UNINSTALL" in source
    assert "NO - CANCEL AND KEEP THE APPLICATION" in source


def test_installer_and_shortcuts_use_the_dairyos_cow_icon():
    source = _source()

    assert "SetupIconFile=..\\..\\assets\\dairyos-cow.ico" in source
    assert "UninstallDisplayIcon={app}\\dairyos-cow.ico" in source
    assert source.count('IconFilename: "{app}\\dairyos-cow.ico"') == 2
