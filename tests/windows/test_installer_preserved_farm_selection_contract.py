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
        "function SelectedFarmCandidate(): String;",
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


def test_action_page_precedes_conditional_farm_page():
    source = _source()

    init = _block(
        source,
        "procedure InitializeWizard();",
        "function NextButtonClick(CurPageID: Integer): Boolean;",
    )

    data_pos = init.index("DataChoicePage := CreateInputOptionPage(")
    farm_pos = init.index("FarmChoicePage := CreateInputOptionPage(")

    assert data_pos < farm_pos
    assert "      DataChoicePage.ID," in init


def test_multiple_farms_without_pointer_require_explicit_selection():
    source = _source()

    init = _block(
        source,
        "procedure InitializeWizard();",
        "function NextButtonClick(CurPageID: Integer): Boolean;",
    )

    assert "ConfiguredRoot := ConfiguredDairyOSDataRoot()" in init
    assert "if InitialFarmIndex >= 0 then" in init
    assert "else if GetArrayLength(FarmCandidatePaths) = 1 then" in init
    assert "FarmChoicePage.SelectedValueIndex := -1" in init

    # Canonical fallback must not manufacture a configured identity.
    assert "ConfiguredRoot := ExistingDairyOSDataRoot()" not in init


def test_genuine_configured_farm_is_visibly_identified():
    source = _source()

    init = _block(
        source,
        "procedure InitializeWizard();",
        "function NextButtonClick(CurPageID: Integer): Boolean;",
    )

    assert "[Currently configured]" in init
    assert "'Farm data: ' + FarmCandidatePaths[I]" in init


def test_keep_and_restore_select_exact_farm_on_farm_page():
    source = _source()

    handler = _block(
        source,
        "function NextButtonClick(CurPageID: Integer): Boolean;",
        "function ShouldSkipPage(PageID: Integer): Boolean;",
    )

    farm_transition = re.search(
        r"if \(FarmChoicePage <> nil\) and "
        r"\(CurPageID = FarmChoicePage\.ID\) then"
        r"(.*?)"
        r"if CurPageID = CleanConfirmationPage\.ID then",
        handler,
        flags=re.DOTALL,
    )
    assert farm_transition is not None

    block = farm_transition.group(1)
    assert "FarmRoot := SelectedFarmCandidate()" in block
    assert "SelectedDataRoot := FarmRoot" in block
    assert "ExistingDairyOSDataRoot()" not in block


def test_farm_page_is_only_shown_for_keep_or_restore():
    source = _source()

    skip = _block(
        source,
        "function ShouldSkipPage(PageID: Integer): Boolean;",
        "function ShouldLaunchDairyOS(): Boolean;",
    )

    assert "(FarmChoicePage <> nil)" in skip
    assert "(not ExistingDataDetected)" in skip
    assert "DataChoicePage.SelectedValueIndex <> 0" in skip
    assert "DataChoicePage.SelectedValueIndex <> RestoreChoiceIndex" in skip


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

def test_farm_candidate_display_includes_path_type_and_configured_status():
    source = _source()

    assert "CandidateLabel: String;" in source
    assert "' [Primary farm]'" in source
    assert "' [Preserved separate farm]'" in source
    assert "' [Currently configured]'" in source
    assert "Lowercase(CanonicalDairyOSDataRoot())" in source
    assert "FarmChoicePage.Add(CandidateLabel);" in source
