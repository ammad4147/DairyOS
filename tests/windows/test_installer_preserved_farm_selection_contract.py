from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "tools" / "windows-desktop" / "DairyOS-Installer.iss"


def _source() -> str:
    return INSTALLER.read_text(encoding="utf-8")


def _block(source: str, start: str, end: str) -> str:
    match = re.search(
        re.escape(start) + r"(.*?)" + re.escape(end),
        source,
        flags=re.DOTALL,
    )
    assert match is not None, f"missing block: {start}"
    return match.group(1)


def test_configured_root_is_distinct_from_canonical_fallback():
    source = _source()

    configured = _block(
        source,
        "function ConfiguredDairyOSDataRoot(): String;",
        "function ExistingDairyOSDataRoot(): String;",
    )
    existing = _block(
        source,
        "function ExistingDairyOSDataRoot(): String;",
        "function AllocateNewDairyOSDataRoot(): String;",
    )

    assert "'DAIRYOS_DATA_DIR'" in configured
    assert "Result := ''" in configured
    assert "Result := ConfiguredRoot" in configured
    assert "CanonicalDairyOSDataRoot()" not in configured

    assert "ConfiguredDairyOSDataRoot()" in existing
    assert "CanonicalDairyOSDataRoot()" in existing


def test_installer_discovers_canonical_and_owned_sibling_farm_roots():
    source = _source()

    scan = _block(
        source,
        "procedure ScanKnownFarmRoots();",
        "procedure ScanKnownBackupRoots();",
    )

    assert "SetArrayLength(FarmCandidatePaths, 0)" in scan
    assert "ConfiguredRoot := ConfiguredDairyOSDataRoot()" in scan
    assert "AddFarmCandidate(ConfiguredRoot)" in scan
    assert (
        "AddFarmCandidate(AddBackslash(CommonDataRoot) + 'DairyOS')"
        in scan
    )
    assert "'DairyOS-New-*'" in scan

    assert "ExpandConstant('{commonappdata}')" in scan
    assert "GetLogicalDriveStrings" not in scan
    assert "DAIRYOS_RECOVERY_ROOT" not in scan



def test_farm_candidate_requires_recognizable_dairyos_state():
    source = _source()

    validator = _block(
        source,
        "function IsRecognizedDairyOSFarmRoot(const Root: String): Boolean;",
        "procedure AddFarmCandidate(const Candidate: String);",
    )

    assert "FileExists(AddBackslash(Root) + 'installation_state.json')" in validator
    assert "FileExists(AddBackslash(Root) + 'lifecycle.json')" in validator
    assert "DirExists(AddBackslash(Root) + 'postgres\\data')" in validator
    assert "DirectoryHasEntries(AddBackslash(Root) + 'storage')" in validator
    result_expression = validator[validator.index("Result :="):]
    assert "postmaster.pid" not in result_expression


def test_preserved_data_detection_requires_a_validated_farm_root():
    source = _source()

    detection = _block(
        source,
        "function DetectExistingDairyOSData(): Boolean;",
        "procedure InitializeWizard();",
    )

    assert "GetArrayLength(FarmCandidatePaths) > 0" in detection
    assert "localappdata" not in detection.lower()
    assert "ExistingDairyOSDataRoot()" not in detection


def test_action_page_precedes_direct_backup_selection():
    source = _source()

    init = _block(
        source,
        "procedure InitializeWizard();",
        "function NextButtonClick(CurPageID: Integer): Boolean;",
    )

    data_pos = init.index("DataChoicePage := CreateInputOptionPage(")
    backup_pos = init.index("BackupChoicePage := CreateInputOptionPage(")

    assert data_pos < backup_pos

    # Backup selection is directly parented to the action page.
    backup = init[backup_pos:]
    assert "DataChoicePage.ID," in backup

    # No intermediate farm-selection page exists.
    assert "FarmChoicePage" not in init



def test_discovered_farms_without_pointer_do_not_authorize_continue():
    source = _source()

    init = _block(
        source,
        "procedure InitializeWizard();",
        "function NextButtonClick(CurPageID: Integer): Boolean;",
    )

    assert "ConfiguredRoot := ConfiguredDairyOSDataRoot()" in init
    assert "if (ConfiguredRoot <> '') and" in init
    assert "IsRecognizedDairyOSFarmRoot(ConfiguredRoot) then" in init
    assert "if ExistingDataDetected then" not in init

    # Discovery remains internal backup-discovery authority only.
    assert "FarmCandidatePaths" not in init
    assert "FarmChoicePage" not in init
    assert "InitialFarmIndex" not in init
    assert "CandidateLabel" not in init

    # Canonical fallback must never manufacture previous-farm identity.
    assert "ConfiguredRoot := ExistingDairyOSDataRoot()" not in init



def test_genuine_configured_farm_is_authoritative_without_being_presented():
    source = _source()

    init = _block(
        source,
        "procedure InitializeWizard();",
        "function NextButtonClick(CurPageID: Integer): Boolean;",
    )
    handler = _block(
        source,
        "function NextButtonClick(CurPageID: Integer): Boolean;",
        "function ShouldSkipPage(PageID: Integer): Boolean;",
    )

    # The genuine configured farm controls whether Continue is offered.
    assert "ConfiguredRoot := ConfiguredDairyOSDataRoot()" in init
    assert "if (ConfiguredRoot <> '') and" in init
    assert "IsRecognizedDairyOSFarmRoot(ConfiguredRoot) then" in init
    assert "DataChoicePage.Add('Continue with Existing Farm');" in init

    # Continue resolves the exact configured farm automatically.
    keep_start = handler.index("if (KeepChoiceIndex >= 0) and")
    restore_start = handler.index(
        "if (RestoreChoiceIndex >= 0) and",
        keep_start,
    )
    keep = handler[keep_start:restore_start]

    assert "FarmRoot := ConfiguredDairyOSDataRoot()" in keep
    assert "IsRecognizedDairyOSFarmRoot(FarmRoot)" in keep
    assert "SelectedInstallMode := 'keep'" in keep
    assert "SelectedDataRoot := FarmRoot" in keep

    # Configured identity is authority, not an operator selection label.
    assert "[Currently configured]" not in source
    assert "'Farm data: ' + FarmCandidatePaths[I]" not in source
    assert "FarmChoicePage" not in source




def test_continue_and_restore_have_separate_destination_authorities():
    source = _source()

    handler = _block(
        source,
        "function NextButtonClick(CurPageID: Integer): Boolean;",
        "function ShouldSkipPage(PageID: Integer): Boolean;",
    )

    keep_start = handler.index("if (KeepChoiceIndex >= 0) and")
    restore_start = handler.index(
        "if (RestoreChoiceIndex >= 0) and",
        keep_start,
    )
    new_start = handler.index(
        "SelectedInstallMode := 'new';",
        restore_start,
    )

    keep = handler[keep_start:restore_start]
    restore = handler[restore_start:new_start]

    # Continue resumes the exact configured existing farm.
    assert "FarmRoot := ConfiguredDairyOSDataRoot()" in keep
    assert "IsRecognizedDairyOSFarmRoot(FarmRoot)" in keep
    assert "SelectedInstallMode := 'keep'" in keep
    assert "SelectedDataRoot := FarmRoot" in keep
    assert "SelectNewDairyOSDataRoot()" not in keep
    assert "SelectedBackupPath" not in keep

    # Restore always receives a separate DairyOS-owned target.
    assert "SelectedInstallMode := 'restore'" in restore
    assert "SelectedDataRoot := SelectNewDairyOSDataRoot()" in restore
    assert "SelectedDataRoot := ''" not in restore

    # Neither path uses an operator farm-selection surface.
    assert "FarmChoicePage" not in source
    assert "SelectedFarmCandidate" not in source



def test_keep_is_operator_reachable_without_farm_selection():
    source = _source()

    init = _block(
        source,
        "procedure InitializeWizard();",
        "function NextButtonClick(CurPageID: Integer): Boolean;",
    )
    handler = _block(
        source,
        "function NextButtonClick(CurPageID: Integer): Boolean;",
        "function ShouldSkipPage(PageID: Integer): Boolean;",
    )

    assert "KeepChoiceIndex: Integer;" in source
    assert "KeepChoiceIndex := -1;" in init
    assert "DataChoicePage.Add('Continue with Existing Farm');" in init

    # Continue exists only for the surviving configured farm.
    assert "if (ConfiguredRoot <> '') and" in init
    assert "IsRecognizedDairyOSFarmRoot(ConfiguredRoot) then" in init
    assert "if ExistingDataDetected then" not in init

    keep_start = handler.index("if (KeepChoiceIndex >= 0) and")
    restore_start = handler.index(
        "if (RestoreChoiceIndex >= 0) and",
        keep_start,
    )
    keep = handler[keep_start:restore_start]

    assert "DataChoicePage.SelectedValueIndex = KeepChoiceIndex" in keep
    assert "FarmRoot := ConfiguredDairyOSDataRoot()" in keep
    assert "IsRecognizedDairyOSFarmRoot(FarmRoot)" in keep
    assert "SelectedInstallMode := 'keep'" in keep
    assert "SelectedDataRoot := FarmRoot" in keep
    assert "SelectedDataRoot := ''" not in keep
    assert "SelectNewDairyOSDataRoot()" not in keep
    assert "Continue cannot guess another farm" in keep

    assert "FarmChoicePage" not in source
    assert "SelectedFarmCandidate" not in source


    # This contract deliberately fails against the previously certified
    # implementation where --choice-mode keep existed but no wizard action
    # could ever select it.


def test_restore_without_preserved_farm_uses_new_dairyos_owned_root():
    source = _source()

    handler = _block(
        source,
        "function NextButtonClick(CurPageID: Integer): Boolean;",
        "function ShouldSkipPage(PageID: Integer): Boolean;",
    )

    assert "SelectedInstallMode := 'restore'" in handler
    assert "SelectedDataRoot := SelectNewDairyOSDataRoot()" in handler


def test_backups_are_discovered_from_every_validated_farm_root():
    source = _source()

    scan = _block(
        source,
        "procedure ScanKnownBackupRoots();",
        "function DetectExistingDairyOSData(): Boolean;",
    )

    assert (
        "for I := 0 to GetArrayLength(FarmCandidatePaths) - 1 do"
        in scan
    )
    assert (
        "AddBackslash(FarmCandidatePaths[I]) + 'backups'"
        in scan
    )
    assert "DAIRYOS_BACKUP_MIRROR_ROOT" in scan
    assert "DAIRYOS_RECOVERY_ROOT" in scan


def test_new_empty_farm_remains_non_destructive_sibling_allocation():
    source = _source()

    assert "function AllocateNewDairyOSDataRoot(): String;" in source
    assert "ExpandConstant('{commonappdata}\\DairyOS-New-')" in source
    assert "SelectedInstallMode := 'clean'" in source
    assert "SelectedDataRoot := AllocateNewDairyOSDataRoot()" in source

    uninstall_delete = _block(source, "[UninstallDelete]", "[Code]")
    active_rules = "\n".join(
        line
        for line in uninstall_delete.splitlines()
        if line.strip() and not line.lstrip().startswith(";")
    )
    assert "DairyOS" not in active_rules


def test_downstream_authority_remains_selected_data_root():
    source = _source()

    resolver = _block(
        source,
        "function DairyOSDataRoot(Param: String): String;",
        "procedure ProvisionLifecycleState();",
    )

    assert "if SelectedDataRoot <> '' then" in resolver
    assert "Result := SelectedDataRoot" in resolver

    assert 'ValueData: "{code:DairyOSDataRoot}"' in source
    assert '--data-root ""{code:DairyOSDataRoot}""' in source


def test_backup_selection_requires_valid_explicit_index():
    source = _source()

    handler = _block(
        source,
        "function NextButtonClick(CurPageID: Integer): Boolean;",
        "function ShouldSkipPage(PageID: Integer): Boolean;",
    )

    assert "BackupChoicePage.SelectedValueIndex < 0" in handler
    assert (
        "BackupChoicePage.SelectedValueIndex >="
        in handler
    )
    assert (
        "BackupCandidatePaths[BackupChoicePage.SelectedValueIndex]"
        in handler
    )

def test_farm_candidates_remain_internal_and_are_not_presented():
    source = _source()

    # Recognized farm roots remain internal discovery authorities.
    assert "FarmCandidatePaths: array of String;" in source
    assert "procedure ScanKnownFarmRoots();" in source
    assert "procedure ScanKnownBackupRoots();" in source

    backup_scan = _block(
        source,
        "procedure ScanKnownBackupRoots();",
        "function DetectExistingDairyOSData(): Boolean;",
    )

    assert (
        "for I := 0 to GetArrayLength(FarmCandidatePaths) - 1 do"
        in backup_scan
    )
    assert (
        "AddBackslash(FarmCandidatePaths[I]) + 'backups'"
        in backup_scan
    )

    # Discovery must never become an operator destination list.
    assert "CandidateLabel" not in source
    assert "' [Primary farm]'" not in source
    assert "' [Preserved separate farm]'" not in source
    assert "' [Currently configured]'" not in source
    assert "FarmChoicePage" not in source
    assert "SelectedFarmCandidate" not in source



def test_keep_skips_new_confirmation_and_backup_and_uses_exact_farm():
    source = _source()

    handler = _block(
        source,
        "function NextButtonClick(CurPageID: Integer): Boolean;",
        "function ShouldSkipPage(PageID: Integer): Boolean;",
    )
    skip = _block(
        source,
        "function ShouldSkipPage(PageID: Integer): Boolean;",
        "function ShouldLaunchDairyOS(): Boolean;",
    )

    keep_start = handler.index("if (KeepChoiceIndex >= 0) and")
    restore_start = handler.index(
        "if (RestoreChoiceIndex >= 0) and",
        keep_start,
    )
    keep = handler[keep_start:restore_start]

    assert "FarmRoot := ConfiguredDairyOSDataRoot()" in keep
    assert "SelectedDataRoot := FarmRoot" in keep
    assert "SelectNewDairyOSDataRoot()" not in keep
    assert "SelectedBackupPath" not in keep

    # There is no farm-selection page for any mode.
    assert "FarmChoicePage" not in source

    # New confirmation is reachable only for New Installation.
    clean_start = skip.index("if PageID = CleanConfirmationPage.ID then")
    backup_start = skip.index(
        "if PageID = BackupChoicePage.ID then",
        clean_start,
    )
    clean = skip[clean_start:backup_start]

    assert "(not ExistingDataDetected) or" in clean
    assert "(DataChoicePage.SelectedValueIndex <> 0)" in clean

    # BackupChoicePage belongs exclusively to Restore.
    backup = skip[backup_start:]
    assert "DataChoicePage.SelectedValueIndex <> RestoreChoiceIndex" in backup
    assert "KeepChoiceIndex" not in backup


def test_keep_staging_never_uses_backup_path():
    source = _source()

    keep_start = source.index("else if SelectedInstallMode = 'keep' then")
    new_start = source.index(
        "else if SelectedInstallMode = 'new' then",
        keep_start,
    )
    keep_block = source[keep_start:new_start]

    assert "--choice-mode keep" in keep_block
    assert "--data-root" in keep_block
    assert "--backup-path" not in keep_block
    assert "SelectedBackupPath" not in keep_block


def test_restore_always_targets_separate_new_dairyos_root():
    source = _source()

    handler = _block(
        source,
        "function NextButtonClick(CurPageID: Integer): Boolean;",
        "function ShouldSkipPage(PageID: Integer): Boolean;",
    )

    restore_start = handler.index(
        "if (RestoreChoiceIndex >= 0) and"
    )
    new_start = handler.index(
        "SelectedInstallMode := 'new';",
        restore_start,
    )
    restore = handler[restore_start:new_start]

    assert "SelectedInstallMode := 'restore'" in restore
    assert "SelectedDataRoot := SelectNewDairyOSDataRoot()" in restore

    # Restore cannot target a discovered/configured existing farm.
    assert "FarmChoicePage" not in restore
    assert "SelectedFarmCandidate" not in restore
    assert "FarmCandidatePaths" not in restore
    assert "ConfiguredDairyOSDataRoot()" not in restore
    assert "SelectedDataRoot := ''" not in restore




def test_restore_presentation_is_verified_backup_selection_only():
    source = _source()

    assert "'Saved Backups'" in source
    assert "'Choose a backup by date and time.'" in source
    assert (
        "'The newest backup is first. DairyOS checks the selected backup "
        "again before restoring it.'"
        in source
    )

    # No destination/farm-selection presentation survives.
    assert "'DairyOS Restore Destination'" not in source
    assert "'Choose the DairyOS farm to restore.'" not in source
    assert (
        "'Select the exact DairyOS farm that will receive the chosen "
        "verified backup.'"
        not in source
    )
    assert "FarmChoicePage" not in source


def test_continue_requires_recognized_configured_previous_farm():
    source = _source()

    init = _block(
        source,
        "procedure InitializeWizard();",
        "function NextButtonClick(CurPageID: Integer): Boolean;",
    )

    continue_add = init.index(
        "DataChoicePage.Add('Continue with Existing Farm');"
    )
    authority_start = init.rfind(
        "if (ConfiguredRoot <> '') and",
        0,
        continue_add,
    )

    assert authority_start >= 0

    authority = init[authority_start:continue_add]

    assert "IsRecognizedDairyOSFarmRoot(ConfiguredRoot)" in authority
    assert "ExistingDataDetected" not in authority


def test_continue_never_uses_discovered_farm_list_or_newest_heuristic():
    source = _source()

    handler = _block(
        source,
        "function NextButtonClick(CurPageID: Integer): Boolean;",
        "function ShouldSkipPage(PageID: Integer): Boolean;",
    )

    keep_start = handler.index("if (KeepChoiceIndex >= 0) and")
    restore_start = handler.index(
        "if (RestoreChoiceIndex >= 0) and",
        keep_start,
    )
    keep = handler[keep_start:restore_start]

    assert "ConfiguredDairyOSDataRoot()" in keep
    assert "SelectedFarmCandidate()" not in keep
    assert "FarmCandidatePaths" not in keep
    assert "BackupCandidatePaths" not in keep
    assert "SelectedBackupPath" not in keep
    assert "GetDateTimeString" not in keep
    assert "FindFirst" not in keep


def test_backup_selection_is_restore_only_and_farm_selection_is_absent():
    source = _source()

    skip = _block(
        source,
        "function ShouldSkipPage(PageID: Integer): Boolean;",
        "function ShouldLaunchDairyOS(): Boolean;",
    )

    # Farm-selection UI has been fully retired.
    assert "FarmChoicePage" not in source
    assert "SelectedFarmCandidate" not in source

    # Backup selection is the sole Restore-specific selection page.
    backup_start = skip.index("if PageID = BackupChoicePage.ID then")
    backup = skip[backup_start:]

    assert "RestoreChoiceIndex" in backup
    assert "KeepChoiceIndex" not in backup
    assert "DataChoicePage.SelectedValueIndex <> RestoreChoiceIndex" in backup



def test_new_install_confirmation_navigation_is_not_circular():
    source = _source()

    skip = _block(
        source,
        "function ShouldSkipPage(PageID: Integer): Boolean;",
        "function ShouldLaunchDairyOS(): Boolean;",
    )

    clean_start = skip.index("if PageID = CleanConfirmationPage.ID then")
    backup_start = skip.index(
        "if PageID = BackupChoicePage.ID then",
        clean_start,
    )
    clean = skip[clean_start:backup_start]

    assert "(not ExistingDataDetected) or" in clean
    assert "(DataChoicePage.SelectedValueIndex <> 0)" in clean
    assert "SelectedInstallMode <> 'clean'" not in clean

