
from pathlib import Path

ISS = (
    Path(__file__).parents[2]
    / "tools"
    / "windows-desktop"
    / "DairyOS-Installer.iss"
)


def _source() -> str:
    return ISS.read_text(encoding="utf-8-sig")


def test_canonical_programdata_root_is_single_installer_authority():
    source = _source()

    assert (
        "Result := ExpandConstant('{commonappdata}\\DairyOS');"
        in source
    )
    assert "Result := CanonicalDairyOSDataRoot();" in source

    assert "DairyOS-New-" not in source
    assert "SelectedDataRoot" not in source
    assert "ConfiguredDairyOSDataRoot" not in source
    assert "ExistingDairyOSDataRoot" not in source


def test_installer_does_not_scan_for_preserved_farms():
    source = _source()

    for token in (
        "FarmCandidatePaths",
        "AddFarmCandidate",
        "ScanKnownFarmRoots",
        "DetectExistingDairyOSData",
        "IsRecognizedDairyOSFarmRoot",
    ):
        assert token not in source


def test_installer_does_not_scan_for_recovery_backups():
    source = _source()

    for token in (
        "BackupCandidatePaths",
        "BackupCandidateTimes",
        "AddBackupCandidate",
        "ScanBackupDirectory",
        "ScanKnownBackupRoots",
        "SelectedBackupPath",
    ):
        assert token not in source


def test_installer_does_not_restore_farm_data():
    source = _source()

    for token in (
        "Restore to Verified Backup",
        "--backup-path",
        "pg_restore",
        "StageInstallationChoice",
        "--choice-mode",
        "--lifecycle-choice",
    ):
        assert token not in source


def test_matching_existing_installation_allows_application_refresh():
    source = _source()

    start = source.index(
        "function PrepareToInstall(var NeedsRestart: Boolean): String;"
    )
    end = source.index(
        "function ShouldLaunchDairyOS(): Boolean;"
    )
    block = source[start:end]

    assert "CanonicalDairyOSDataRootHasExistingState()" in block
    assert "ExistingDairyOSInstallationMatches()" in block
    assert "StopInstalledDairyOSForUninstall()" in block
    assert "preserving ProgramData" in block


def test_collision_guard_keeps_unknown_state_fail_closed():
    source = _source()

    start = source.index(
        "function CanonicalDairyOSDataRootHasExistingState(): Boolean;"
    )
    end = source.index(
        "function PrepareToInstall(var NeedsRestart: Boolean): String;"
    )
    block = source[start:end]

    assert "if not DirExists(Root) then" in block
    assert "FindFirst(AddBackslash(Root) + '*', FindRec)" in block
    assert "FindNext(FindRec)" in block
    assert "Result := True;" in block

    assert "lifecycle.json" in block
    assert "LoadStringFromFile(LifecyclePath, AnsiManifest)" in block
    assert '"data_root": "' in block
    assert '"installation_root": "' in block


def test_installer_never_deletes_existing_programdata_to_make_room():
    source = _source()

    assert "DelTree(CanonicalDairyOSDataRoot()" not in source
    assert "RemoveDir(" not in source


def test_refresh_preserves_programdata_and_reprovisions_runtime():
    source = _source()
    assert "preserving ProgramData" in source
    assert "ProvisionLifecycleState();" in source
    assert "ProvisionAutomaticBackupTask();" in source

    assert "[UninstallDelete]" in source
    assert (
        'Type: filesandordirs; Name: "{app}"'
        in source
    )
    assert "ProgramData contains farm data" in source


def test_installer_retains_clean_lifecycle_initialization():
    source = _source()

    assert "procedure ProvisionLifecycleState();" in source
    assert "--lifecycle-install" in source
    assert "--installation-root" in source
    assert "--data-root" in source
    assert "ProvisionLifecycleState();" in source


def test_installer_retains_storage_and_backup_acl_provisioning():
    source = _source()

    for token in (
        "ProvisionLifecycleManifestAcl();",
        "ProvisionStorageTreeAcl();",
        "ProvisionBackupTreeAcl();",
        "ProvisionAutomaticBackupTask();",
    ):
        assert token in source


def test_shortcuts_and_postinstall_launch_use_canonical_resolver():
    source = _source()

    launch_parameter = (
        'Parameters: "--data-root ""{code:DairyOSDataRoot}"""'
    )

    # Start menu, desktop and post-install launch all use the
    # same resolver. Exact count may grow only if another
    # legitimate launcher is intentionally added.
    assert source.count(launch_parameter) >= 3


def test_installer_farm_movement_is_absent_by_design():
    source = _source()

    assert "Continue with Existing Farm" not in source
    assert "Restore to Verified Backup" not in source
    assert "Saved Backups" not in source
    assert "BackupChoicePage" not in source
    assert "DataChoicePage" not in source
