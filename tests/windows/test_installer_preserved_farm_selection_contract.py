
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


def test_matching_existing_installation_compares_windows_paths_case_insensitively():
    source = _source()

    start = source.index("function ExistingDairyOSInstallationMatches(): Boolean;")
    end = source.index("function StopInstalledDairyOSForUninstall(): Boolean; forward;")
    block = source[start:end]

    assert "Pos(Uppercase(" in block
    assert "CanonicalData" in block
    assert "CanonicalInstall" in block
    assert "Uppercase(Manifest)" in block


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
    # Retired Assistant debris must no longer be ignored by the collision
    # guard. It is removed explicitly before the guard executes.
    assert "CompareText(FindRec.Name, 'assistant') <> 0" not in block

    assert "lifecycle.json" in block
    assert "LoadStringFromFile(LifecyclePath, AnsiManifest)" in block
    assert '"data_root": "' in block
    assert '"installation_root": "' in block


def test_installer_never_deletes_existing_programdata_to_make_room():
    source = _source()

    prepare = source[source.index("function PrepareToInstall"):source.index("function ShouldLaunchDairyOS")]
    assert "DelTree(CanonicalDairyOSDataRoot()" not in prepare
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
    assert "farm data remains under its independent backup/recovery ownership" in source


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

    # The existing native DairyOS shortcuts keep their established launch;
    # setup opens the browser-first option after installation.
    assert source.count(launch_parameter) == 2
    assert (
        'Parameters: "--browser --data-root ""{code:DairyOSDataRoot}"""; '
        'Description: "Launch DairyOS Web in your browser"'
    ) in source


def test_installer_farm_movement_is_absent_by_design():
    source = _source()

    assert "Continue with Existing Farm" not in source
    assert "Restore to Verified Backup" not in source
    assert "Saved Backups" not in source
    assert "BackupChoicePage" not in source
    assert "DataChoicePage" not in source


def test_retired_assistant_cleanup_is_narrow_and_runs_after_collision_guard():
    source = _source()

    start = source.index("procedure RemoveRetiredAssistantState();")
    end = source.index("procedure ProvisionLifecycleState();", start)
    cleanup = source[start:end]

    for retired_path in (
        "\\assistant",
        "\\.assistant-staging",
        "\\.assistant-active",
        "\\.assistant-previous",
    ):
        assert retired_path in cleanup

    assert "\\logs\\assistant-llama.log" in cleanup

    # The retirement routine must never delete farm-owned state.
    for protected_path in (
        "\\postgres",
        "\\storage",
        "\\backups",
        "\\lifecycle.json",
    ):
        assert f"DelTree(Root + '{protected_path}'" not in cleanup

    assert "DelTree(Root, " not in cleanup
    assert "RemoveDir(Root" not in cleanup

    prepare_start = source.index(
        "function PrepareToInstall(var NeedsRestart: Boolean): String;"
    )
    prepare_end = source.index(
        "function ShouldLaunchDairyOS(): Boolean;"
    )
    prepare = source[prepare_start:prepare_end]

    cleanup_call = prepare.index("RemoveRetiredAssistantState();")
    collision_check = prepare.index(
        "CanonicalDairyOSDataRootHasExistingState()"
    )

    assert cleanup_call > collision_check


def test_uninstall_removes_retired_assistant_state_without_deleting_farm_root():
    source = _source()

    start = source.index(
        "procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);"
    )
    block = source[start:]

    assert "RemoveRetiredAssistantState();" in block
    assert "DelTree(CanonicalDairyOSDataRoot()" not in block
