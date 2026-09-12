from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ISS = ROOT / "tools" / "windows-desktop" / "DairyOS-Installer.iss"

def _source() -> str:
    return ISS.read_text(encoding="utf-8")

def test_installer_exposes_explicit_data_and_recovery_choices():
    source = _source()

    assert "VersionInfoComments=" not in source
    assert "WizardResizable=" not in source
    assert "WizardSizePercent=140,135" in source
    assert "TInputOptionWizardPage" in source
    assert "Keep existing farm data (recommended)" in source
    assert "Restore from a verified backup" in source
    assert "Start a clean farm" in source
    assert "CLEAN INSTALL DAIRYOS DATA" in source
    assert "Backup candidate (DairyOS verifies before restore)" in source
    assert "No active DairyOS farm was detected, but recovery points are available." in source
    assert "--choice-mode keep" in source
    assert "StageInstallationChoice" in source
    assert "The selected DairyOS installation action could not be recorded." in source
    assert "This page is informational, not a data-choice control." not in source
    assert "WizardForm.Font.Name" not in source
    assert "WizardForm.Font.Size" not in source


def test_install_data_choice_requires_explicit_clean_confirmation_or_backup():
    source = _source()
    start = source.index("function NextButtonClick")
    end = source.index("function ShouldLaunchDairyOS", start)
    block = source[start:end]

    assert "CreateInputQueryPage(" in source
    assert "CleanConfirmationPage.Values[0]" in block
    assert "CLEAN INSTALL DAIRYOS DATA" in block
    assert "SelectedBackupPath" in block
    assert "MsgBox(" in block

def test_uninstall_is_direct_and_keeps_data_without_standalone_admin():
    source = _source()
    assert "PRESERVE FARM DATA AND UNINSTALL" not in source
    assert "Choose how to proceed with DairyOS uninstall" not in source
    assert "beginning straightforward keep-data uninstall" in source
    assert "DairyOS Administration" not in source
    assert "DairyOS-Admin.exe" not in source
    assert "StopInstalledDairyOSForUninstall" in source


def test_installer_user_facing_text_avoids_garbled_unicode_punctuation():
    source = _source()

    assert "•" not in source
    assert "—" not in source


def test_installer_and_shortcuts_use_the_dairyos_cow_icon():
    source = _source()

    assert "SetupIconFile=..\\..\\assets\\dairyos-cow.ico" in source
    assert "UninstallDisplayIcon={app}\\dairyos-cow.ico" in source
    assert source.count('IconFilename: "{app}\\dairyos-cow.ico"') == 2
