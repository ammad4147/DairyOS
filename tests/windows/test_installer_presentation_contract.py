
from pathlib import Path


ISS = (
    Path(__file__).parents[2]
    / "tools"
    / "windows-desktop"
    / "DairyOS-Installer.iss"
)


def _source() -> str:
    return ISS.read_text(encoding="utf-8-sig")


def test_installer_does_not_present_farm_movement_choices():
    source = _source()

    forbidden = (
        "Continue with Existing Farm",
        "Restore to Verified Backup",
        "Saved Backups",
        "DataChoicePage",
        "BackupChoicePage",
        "CleanConfirmationPage",
        "New / Empty Farm",
        "Keep Existing",
    )

    for token in forbidden:
        assert token not in source


def test_existing_canonical_state_produces_clear_fail_closed_message():
    source = _source()

    assert "DairyOS clean installation cannot continue" in source
    assert (
        "Setup will not overwrite, import, restore, select, or adopt existing "
        in source
    )
    assert (
        "farm data. Preserve or remove the existing DairyOS data through the "
        in source
    )
    assert (
        "supported DairyOS Data Management or uninstall workflow"
        in source
    )


def test_installer_does_not_require_clean_install_confirmation_page():
    source = _source()

    assert "function NextButtonClick" not in source
    assert "function ShouldSkipPage" not in source
    assert "CleanConfirmationAccepted" not in source
    assert "CLEAN INSTALL DAIRYOS DATA" not in source
