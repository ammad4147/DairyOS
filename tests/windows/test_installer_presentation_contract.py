from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ISS = ROOT / "tools" / "windows-desktop" / "DairyOS-Installer.iss"

def _source() -> str:
    return ISS.read_text(encoding="utf-8")


def test_installer_exposes_explicit_data_and_recovery_choices():
    source = _source()

    assert "DairyOS Installation" in source
    assert "Choose how to start DairyOS." in source
    assert "DataChoicePage.Add('New Installation');" in source
    assert "DataChoicePage.Add('Continue with Existing Farm');" in source
    assert "DataChoicePage.Add('Restore to Verified Backup');" in source

    # Continue is authorized by the exact surviving configured farm.
    assert "if (ConfiguredRoot <> '') and" in source
    assert "IsRecognizedDairyOSFarmRoot(ConfiguredRoot) then" in source

    # There is no farm-selection presentation for Continue or Restore.
    assert "FarmChoicePage" not in source
    assert "SelectedFarmCandidate" not in source
    assert "'DairyOS Restore Destination'" not in source
    assert "'Choose the DairyOS farm to restore.'" not in source
    assert (
        "'Select the exact DairyOS farm that will receive the chosen "
        "verified backup.'"
        not in source
    )
    assert "'Choose the existing DairyOS farm.'" not in source
    assert (
        "'Select the exact saved DairyOS farm to continue with or restore.'"
        not in source
    )

    # Restore exposes the recovery-point list directly.
    assert "'Saved Backups'" in source
    assert "'Choose a backup by date and time.'" in source





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

    # New must actually be able to reach the confirmation page when
    # recognized existing DairyOS data is present.
    skip_start = source.index("function ShouldSkipPage")
    skip_end = source.index("function ShouldLaunchDairyOS", skip_start)
    skip = source[skip_start:skip_end]

    assert "if PageID = CleanConfirmationPage.ID then" in skip
    assert "(not ExistingDataDetected) or" in skip
    assert "(DataChoicePage.SelectedValueIndex <> 0)" in skip
    assert "(SelectedInstallMode <> 'clean')" not in skip

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
