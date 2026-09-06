from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ISS = ROOT / "tools" / "windows-desktop" / "DairyOS-Installer.iss"


def _source() -> str:
    return ISS.read_text(encoding="utf-8")


def test_installer_exposes_existing_data_and_restore_choices():
    source = _source()

    assert "DetectExistingDairyOSData" in source
    assert "Use existing DairyOS data (recommended)" in source
    assert "Restore a verified backup using DairyOS Administration after installation" in source
    assert "Start a new DairyOS farm" in source
    assert "ShouldLaunchAdminAfterInstall" in source
    assert "The installer itself will not overwrite farm data." in source


def test_uninstaller_explicitly_keeps_data_and_routes_backup_to_admin_tool():
    source = _source()

    assert "DairyOS farm data and the private database are retained by default" in source
    assert "continue uninstall and KEEP all DairyOS data" in source
    assert "create a verified backup first" in source
    assert "DairyOS-Admin.exe" in source
    assert "Permanent data deletion is available only through" in source


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
    assert "/F /T /IM DairyOS.exe" in source
    assert "/F /T /IM DairyOS-Admin.exe" in source
    assert "/F /T /IM DairyOSBackup.exe" in source
    assert "taskkill.exe" in source
    assert "/IM postgres.exe" not in source
    assert 'DairyOS-Automatic-Backup' in source
    assert "Result := StopInstalledDairyOSForUninstall();" in source


def test_ci_does_not_create_preservation_sentinel_before_programdata_bootstrap():
    workflow = (
        ROOT / ".github" / "workflows" / "installer-windows.yml"
    ).read_text(encoding="utf-8")

    early = workflow.index("New-Item -ItemType Directory -Force -Path $dataRoot")
    preflight = workflow.index("$programDataPreflight = Start-Process")
    marker_write = workflow.index('"preserve-me" | Set-Content -Path $marker -Encoding ascii')

    assert early < preflight < marker_write
