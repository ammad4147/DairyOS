
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


def test_existing_canonical_state_is_replaced_for_zero_state_install():
    source = _source()

    assert "zero-state layout" in source
    assert "DelTree(CanonicalDairyOSDataRoot(), True, True, True)" in source
    assert "Backup/export is independent of installation" in source


def test_installer_does_not_require_clean_install_confirmation_page():
    source = _source()

    assert "function NextButtonClick" not in source
    assert "function ShouldSkipPage" not in source
    assert "CleanConfirmationAccepted" not in source
    assert "CLEAN INSTALL DAIRYOS DATA" not in source
