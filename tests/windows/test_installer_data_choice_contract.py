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


def test_installer_exposes_explicit_clean_and_restore_choices():
    source = _source()

    assert "DetectExistingDairyOSData" in source
    assert "CreateInputOptionPage" in source
    assert "Keep existing farm data (recommended)" in source
    assert "Restore from a verified backup" in source
    assert "Start a clean farm" in source
    assert "ScanKnownBackupRoots" in source
    assert "StageInstallationChoice" in source
    assert "TRadioButton" not in source
    assert "ShouldLaunchDairyOS" in source
    assert "--lifecycle-choice" in source
    assert "--choice-mode restore" in source
    assert "--choice-mode clean" in source
    assert "--choice-mode keep" in source
    assert "DairyOS-Admin.exe" not in source


def test_uninstaller_explicitly_keeps_data_without_standalone_admin():
    source = _source()

    assert "YES - PRESERVE FARM DATA AND UNINSTALL" in source
    assert "Choose a destination for a verified farm-data package" in source
    assert "NO - CANCEL AND KEEP THE APPLICATION" in source
    assert "GetDateTimeString('yyyymmdd-hhnnss', '', '')" in source
    assert "BrowseForFolder(" in source
    assert "SelectDirectory(" not in source
    assert "DairyOS-Admin.exe" not in source


def test_silent_uninstall_bypasses_interactive_data_prompt():
    source = _source()

    assert "function IsSilentUninstall(): Boolean;" in source
    assert "ParamCount" in source
    assert "ParamStr(I)" in source
    assert "(Param = '/SILENT') or (Param = '/VERYSILENT')" in source
    assert "if IsSilentUninstall() then" in source
    assert "if WizardSilent() then" not in source


def test_uninstall_stops_only_dairyos_private_cluster_and_runtime_processes():
    source = _source()

    assert "function StopInstalledDairyOSForUninstall(): Boolean;" in source
    assert "runtime\\PostgreSQL\\bin\\pg_ctl.exe" in source
    assert "DairyOSDataRoot() + '\\postgres\\data'" in source
    assert "postmaster.pid" in source
    assert "stop -m fast -w -t 30" in source
    assert "Get-CimInstance Win32_Process" in source
    assert "StopInstalledProcessByPath(ExpandConstant('{app}\\DairyOS.exe'))" in source
    assert "StopInstalledProcessByPath(ExpandConstant('{app}\\DairyOSBackup.exe'))" in source
    assert "taskkill.exe" not in source
    assert "/IM postgres.exe" not in source
    assert 'DairyOS-Automatic-Backup' in source
    assert "Result := StopInstalledDairyOSForUninstall();" in source


def test_uninstall_preservation_archive_is_validated_outside_live_data_root():
    source = _source()

    assert "function IsPathWithinRoot" in source
    assert "Choose a preservation location outside the DairyOS farm-data directory." in source
    assert "if not DirExists(PreservationDestination) then" in source
    assert "System.IO.Compression.ZipFile]::CreateFromDirectory" in source
    assert "System.IO.Compression.ZipFile]::OpenRead" in source
    assert "The preservation package is empty." in source
    assert "Compress-Archive -Path $items" not in source


def test_uninstall_preserves_before_removing_automatic_backup_task():
    source = _source()
    start = source.index("function StopInstalledDairyOSForUninstall")
    end = source.index("function CreatePreservationPackage", start)
    block = source[start:end]

    assert "function RemoveInstalledBackupTask(): Boolean;" in source
    assert "schtasks.exe" in source
    assert '/Delete /F /TN "DairyOS-Automatic-Backup"' in source
    assert '/Query /TN "DairyOS-Automatic-Backup"' in source
    assert block.index("if not CreatePreservationPackage() then") < block.index(
        "if not RemoveInstalledBackupTask() then"
    )


def test_unattended_uninstall_can_exercise_the_verified_preservation_path():
    source = _source()

    assert "DAIRYOS_UNINSTALL_PRESERVATION_DESTINATION" in source
    assert "PreservationDestination := GetEnv('DAIRYOS_UNINSTALL_PRESERVATION_DESTINATION');" in source
    assert "BrowseForFolder(" in source


def test_ci_does_not_create_preservation_sentinel_before_programdata_bootstrap():
    workflow = (
        ROOT / ".github" / "workflows" / "installer-windows.yml"
    ).read_text(encoding="utf-8")

    early = workflow.index("New-Item -ItemType Directory -Force -Path $dataRoot")
    preflight = workflow.index("$programDataPreflight = Start-Process")
    marker_write = workflow.index('"preserve-me" | Set-Content -Path $marker -Encoding ascii')

    assert early < preflight < marker_write


def test_new_install_stages_explicit_clean_bootstrap_while_keep_stays_non_destructive():
    source = _source()

    keep = source.index("else if SelectedInstallMode = 'keep' then")
    new = source.index("else if SelectedInstallMode = 'new' then", keep)
    keep_block = source[keep:new]
    new_end = source.index("  else\n    exit;", new)
    new_block = source[new:new_end]

    assert "--choice-mode keep" in keep_block
    assert "--choice-mode clean" in new_block
    assert "SelectedInstallMode = 'new'" not in keep_block
