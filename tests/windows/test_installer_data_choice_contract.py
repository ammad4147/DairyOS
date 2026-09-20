
from pathlib import Path

ISS = (
    Path(__file__).parents[2]
    / "tools"
    / "windows-desktop"
    / "DairyOS-Installer.iss"
)


def _source() -> str:
    return ISS.read_text(encoding="utf-8-sig")


def test_installer_refreshes_matching_installation_and_rejects_unknown_state():
    source = _source()

    forbidden = (
        "DataChoicePage",
        "BackupChoicePage",
        "SelectedInstallMode",
        "SelectedBackupPath",
        "SelectedDataRoot",
        "CleanConfirmationPage",
        "CleanConfirmationAccepted",
        "KeepChoiceIndex",
        "RestoreChoiceIndex",
        "Continue with Existing Farm",
        "Restore to Verified Backup",
    )

    for token in forbidden:
        assert token not in source
    assert "ExistingDairyOSInstallationMatches" in source
    assert "preserving ProgramData" in source


def test_installer_uses_one_canonical_programdata_root():
    source = _source()

    assert "function CanonicalDairyOSDataRoot(): String;" in source
    assert (
        "Result := ExpandConstant('{commonappdata}\\DairyOS');"
        in source
    )

    resolver_start = source.index(
        "function DairyOSDataRoot(Param: String): String;"
    )
    resolver_end = source.index(
        "procedure ProvisionLifecycleState();"
    )
    resolver = source[resolver_start:resolver_end]

    assert "Result := CanonicalDairyOSDataRoot();" in resolver
    assert "SelectedDataRoot" not in resolver
    assert "ConfiguredDairyOSDataRoot" not in resolver
    assert "ExistingDairyOSDataRoot" not in resolver


def test_installer_does_not_allocate_alternate_farm_roots():
    source = _source()

    forbidden = (
        "DairyOS-New-",
        "AllocateNewDairyOSDataRoot",
        "SelectNewDairyOSDataRoot",
    )

    for token in forbidden:
        assert token not in source

    # Timestamp generation is valid for operator-selected portable package
    # filenames. It must never participate in resolving the live farm root.
    resolver_start = source.index(
        "function DairyOSDataRoot(Param: String): String;"
    )
    resolver_end = source.index(
        "procedure ProvisionLifecycleState();"
    )
    resolver = source[resolver_start:resolver_end]
    assert "GetDateTimeString(" not in resolver

    guard_start = source.index(
        "function CanonicalDairyOSDataRootHasExistingState(): Boolean;"
    )
    guard_end = source.index(
        "function PrepareToInstall(var NeedsRestart: Boolean): String;"
    )
    guard = source[guard_start:guard_end]
    assert "GetDateTimeString(" not in guard


def test_installer_does_not_discover_or_select_existing_farms():
    source = _source()

    forbidden = (
        "FarmCandidatePaths",
        "AddFarmCandidate",
        "ScanKnownFarmRoots",
        "DetectExistingDairyOSData",
        "IsRecognizedDairyOSFarmRoot",
    )

    for token in forbidden:
        assert token not in source


def test_installer_does_not_discover_or_select_backups():
    source = _source()

    forbidden = (
        "BackupCandidatePaths",
        "BackupCandidateTimes",
        "AddBackupCandidate",
        "ScanBackupDirectory",
        "ScanKnownBackupRoots",
        "SelectedBackupPath",
        "--backup-path",
        "pg_restore",
    )

    for token in forbidden:
        assert token not in source


def test_installer_no_longer_stages_installation_choice():
    source = _source()

    forbidden = (
        "StageInstallationChoice",
        "ProvisionInstallationChoiceAcl",
        "pending-installation-choice",
        "--lifecycle-choice",
        "--choice-mode",
    )

    for token in forbidden:
        assert token not in source


def test_unknown_existing_canonical_root_is_rejected():
    source = _source()

    assert (
        "function CanonicalDairyOSDataRootHasExistingState(): Boolean;"
        in source
    )
    assert (
        "function PrepareToInstall(var NeedsRestart: Boolean): String;"
        in source
    )

    prepare_start = source.index(
        "function PrepareToInstall(var NeedsRestart: Boolean): String;"
    )
    prepare_end = source.index(
        "function ShouldLaunchDairyOS(): Boolean;"
    )
    prepare = source[prepare_start:prepare_end]

    assert "CanonicalDairyOSDataRootHasExistingState()" in prepare
    assert "not tied to this existing DairyOS installation" in prepare
    assert "ExistingDairyOSInstallationMatches()" in prepare
    assert "DelTree(CanonicalDairyOSDataRoot()" not in prepare
    assert "CanonicalDairyOSDataRoot()" in prepare


def test_canonical_root_guard_checks_entries_not_directory_existence_alone():
    source = _source()

    start = source.index(
        "function CanonicalDairyOSDataRootHasExistingState(): Boolean;"
    )
    end = source.index(
        "function PrepareToInstall(var NeedsRestart: Boolean): String;"
    )
    guard = source[start:end]

    assert "if not DirExists(Root) then" in guard
    assert "FindFirst(AddBackslash(Root) + '*', FindRec)" in guard
    assert "(FindRec.Name <> '.')" in guard
    assert "(FindRec.Name <> '..')" in guard
    assert "Result := True;" in guard


def test_post_install_and_launch_use_canonical_data_root():
    source = _source()

    assert (
        'Parameters: "--data-root ""{code:DairyOSDataRoot}"""'
        in source
    )
    assert (
        "'--data-root \"' + DairyOSDataRoot('') + '\"'"
        in source
    )

    assert (
        "LifecyclePath := DairyOSDataRoot('') + '\\lifecycle.json';"
        in source
    )
    assert (
        "BackupPath := DairyOSDataRoot('') + '\\backups';"
        in source
    )
    assert (
        "StoragePath := DairyOSDataRoot('') + '\\storage';"
        in source
    )
