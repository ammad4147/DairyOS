from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ISS = ROOT / "tools" / "windows-desktop" / "DairyOS-Installer.iss"


def _source() -> str:
    return ISS.read_text(encoding="utf-8")


def test_release_build_has_one_staged_folder_and_clickable_setup_beside_it():
    build = (ROOT / "scripts" / "Build-DairyOS-Installer.ps1").read_text(
        encoding="utf-8-sig"
    )
    source = _source()

    assert '"dist\\DairyOS-Release\\DairyOS"' in build
    assert '"dist\\DairyOS-Release\\DairyOS-Windows-Installer.exe"' in build
    assert "dist\\DairyOS-Installer" not in build
    assert "OutputDir=..\\..\\dist\\DairyOS-Release" in source
    assert "Source: \"..\\..\\dist\\DairyOS-Release\\DairyOS\\*\"" in source
    assert '("/O" + (Split-Path -Parent $outputPath))' in build
    assert '("/DSourceCommit=$($releaseManifest.source_commit)")' in build
    assert '("/DSourceTree=$($releaseManifest.source_tree)")' in build
    assert '"-o" + (Split-Path -Parent $outputPath)' not in build
    assert '"-dSourceCommit=' not in build
    assert '"-dSourceTree=' not in build



def test_installer_exposes_operator_reachable_new_keep_and_restore_choices():
    source = _source()

    assert "DetectExistingDairyOSData" in source
    assert "CreateInputOptionPage" in source
    assert "DataChoicePage.Add('New Installation');" in source
    assert "DataChoicePage.Add('Continue with Existing Farm');" in source
    assert "DataChoicePage.Add('Restore to Verified Backup');" in source
    assert "KeepChoiceIndex := 1;" in source
    assert "RestoreChoiceIndex := DataChoicePage.CheckListBox.Items.Count - 1;" in source

    # Continue is authorized only by the exact surviving configured farm,
    # not merely by discovery of any preserved DairyOS farm.
    assert "if (ConfiguredRoot <> '') and" in source
    assert "IsRecognizedDairyOSFarmRoot(ConfiguredRoot) then" in source

    assert "ScanKnownBackupRoots" in source
    assert "StageInstallationChoice" in source
    assert "TRadioButton" not in source
    assert "ShouldLaunchDairyOS" in source
    assert "--lifecycle-choice" in source
    assert "--choice-mode restore" in source
    assert "--choice-mode new" in source
    assert "--choice-mode keep" in source
    assert "DairyOS-Admin.exe" not in source

def test_uninstaller_is_straightforward_and_keeps_programdata_in_place():
    source = _source()

    assert "beginning straightforward keep-data uninstall" in source
    assert "Result := StopInstalledDairyOSForUninstall();" in source
    assert "PRESERVE FARM DATA AND UNINSTALL" not in source
    assert "BrowseForFolder(" not in source
    assert "CreatePreservationPackage" not in source
    assert "DairyOS-Farm-Preservation-" not in source
    assert "[UninstallDelete]\n; Deliberately empty." in source
    assert "DairyOS-Admin.exe" not in source


def test_uninstall_has_no_custom_interactive_or_silent_data_prompt():
    source = _source()

    assert "function IsSilentUninstall(): Boolean;" not in source
    assert "DAIRYOS_UNINSTALL_PRESERVATION_DESTINATION" not in source
    assert "Choose how to proceed with DairyOS uninstall" not in source


def test_uninstall_stops_only_dairyos_private_cluster_and_runtime_processes():
    source = _source()

    assert "function StopInstalledDairyOSForUninstall(): Boolean;" in source
    assert "runtime\\PostgreSQL\\bin\\pg_ctl.exe" in source
    assert "DairyOSDataRoot('') + '\\postgres\\data'" in source
    assert "postmaster.pid" in source
    assert "stop -m fast -w -t 30" in source
    assert "Get-CimInstance Win32_Process" in source
    assert "StopInstalledProcessByPath(ExpandConstant('{app}\\DairyOS.exe'))" in source
    assert "StopInstalledProcessByPath(ExpandConstant('{app}\\DairyOSBackup.exe'))" in source
    assert "taskkill.exe" not in source
    assert "/IM postgres.exe" not in source
    assert 'DairyOS-Automatic-Backup' in source
    assert "Result := StopInstalledDairyOSForUninstall();" in source


def test_uninstall_removes_automatic_backup_task_without_archive_step():
    source = _source()
    start = source.index("function StopInstalledDairyOSForUninstall")
    end = source.index("function InitializeUninstall", start)
    block = source[start:end]

    assert "function RemoveInstalledBackupTask(): Boolean;" in source
    assert "schtasks.exe" in source
    assert '/Delete /F /TN "DairyOS-Automatic-Backup"' in source
    assert '/Query /TN "DairyOS-Automatic-Backup"' in source
    assert "CreatePreservationPackage" not in block
    assert "if not RemoveInstalledBackupTask() then" in block


def test_uninstall_archive_transport_is_absent():
    source = _source()

    assert "PreservationDestination" not in source
    assert "CreatePreservationPackage" not in source
    assert "UninstallDiagnosticPath" not in source
    assert "System.IO.Compression.ZipFile" not in source


def test_ci_does_not_create_retention_sentinel_before_programdata_bootstrap():
    workflow = (
        ROOT / ".github" / "workflows" / "installer-windows.yml"
    ).read_text(encoding="utf-8")

    early = workflow.index("New-Item -ItemType Directory -Force -Path $dataRoot")
    preflight = workflow.index("$programDataPreflight = Start-Process")
    marker_write = workflow.index('"preserve-me" | Set-Content -Path $marker -Encoding ascii')

    assert early < preflight < marker_write


def test_new_install_stages_explicit_non_destructive_bootstrap_while_keep_stays_non_destructive():
    source = _source()

    keep = source.index("else if SelectedInstallMode = 'keep' then")
    new = source.index("else if SelectedInstallMode = 'new' then", keep)
    keep_block = source[keep:new]
    new_end = source.index("  else\n    exit;", new)
    new_block = source[new:new_end]

    assert "--choice-mode keep" in keep_block
    assert "--choice-mode new" in new_block
    assert "SelectedInstallMode = 'new'" not in keep_block


def test_clean_install_uses_a_new_data_root_and_does_not_delete_existing_data():
    source = _source()

    assert "AllocateNewDairyOSDataRoot" in source
    assert "SelectNewDairyOSDataRoot" in source
    assert "CanonicalDairyOSDataRoot" in source
    assert "DAIRYOS_DATA_DIR" in source
    assert "SelectedDataRoot := AllocateNewDairyOSDataRoot()" in source
    assert "ExistingDairyOSDataRoot()" in source
    assert "ValueData: \"{code:DairyOSDataRoot}\"" in source
    assert 'Parameters: "--data-root ""{code:DairyOSDataRoot}"""' in source
    assert "DirectoryHasEntries(Root + '\\backups')" not in source
    assert "arbitrary historical backup trees" in source
    assert "Existing DairyOS records, logs and backups will not be deleted or changed." in source


def test_selected_new_root_is_used_for_post_install_provisioning_and_launch():
    source = _source()

    assert "SelectedDataRoot := AllocateNewDairyOSDataRoot()" in source
    assert "--data-root \"' + DairyOSDataRoot('') + '\"" in source
    assert 'Parameters: "--data-root ""{code:DairyOSDataRoot}"""' in source


def test_separate_empty_farm_uses_runtime_valid_timestamp_separators() -> None:
    """Prevent the Inno runtime Type Mismatch reproduced by INST-LIFECYCLE-01."""
    source = _source()

    broken_runtime_call = "GetDateTimeString('yyyymmdd-hhnnss', '', '')"
    proven_runtime_call = "GetDateTimeString('yyyymmdd-hhnnss', '-', ':')"

    assert broken_runtime_call not in source
    assert source.count(proven_runtime_call) == 1

    allocator_start = source.index("function AllocateNewDairyOSDataRoot(): String;")
    allocator_end = source.index(
        "function DairyOSDataRoot(Param: String): String;",
        allocator_start,
    )
    allocator = source[allocator_start:allocator_end]

    assert proven_runtime_call in allocator
    assert r"ExpandConstant('{commonappdata}\DairyOS-New-')" in allocator
    assert "while DirExists(Candidate) do" in allocator
    assert "Candidate := Base + '-' + IntToStr(Suffix);" in allocator
    assert "Result := Candidate;" in allocator

def test_permanent_shortcuts_pin_the_selected_farm_data_root():
    source = _source()

    icons_start = source.index("[Icons]")
    dirs_start = source.index("[Dirs]", icons_start)
    icons = source[icons_start:dirs_start]

    start_menu = next(
        line
        for line in icons.splitlines()
        if 'Name: "{autoprograms}\\DairyOS"' in line
    )

    desktop = next(
        line
        for line in icons.splitlines()
        if 'Name: "{autodesktop}\\DairyOS"' in line
    )

    selected_root_argument = (
        'Parameters: "--data-root '
        '""{code:DairyOSDataRoot}"""'
    )

    assert selected_root_argument in start_menu
    assert selected_root_argument in desktop


def test_selected_root_has_persistent_and_explicit_launch_authority():
    source = _source()

    assert (
        'ValueName: "DAIRYOS_DATA_DIR"; '
        'ValueData: "{code:DairyOSDataRoot}"'
    ) in source

    explicit_argument = (
        'Parameters: "--data-root '
        '""{code:DairyOSDataRoot}"""'
    )

    assert source.count(explicit_argument) >= 3
