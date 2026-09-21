from pathlib import Path

ISS = Path(__file__).parents[2] / "tools" / "windows-desktop" / "DairyOS-Installer.iss"
WORKFLOW = Path(__file__).parents[2] / ".github" / "workflows" / "installer-windows.yml"


def test_uninstall_has_no_farm_data_preservation_protocol():
    source = ISS.read_text(encoding="utf-8-sig")
    source = source[source.index("function InitializeUninstall"):]
    for token in (
        "PRESERVEFARMDATA", "PRESERVEDATAPATH", "PreserveFarmDataOnUninstall",
        "ChoosePreservationDestination", "ExportFarmDataForUninstall",
        "UninstallPreservationChoiceFromCommandLine",
        "Preserve farm data before uninstalling DairyOS?",
    ):
        assert token not in source


def test_uninstall_retains_runtime_safety_and_removes_application_tree():
    source = ISS.read_text(encoding="utf-8-sig")
    assert "StopInstalledDairyOSForUninstall()" in source
    assert "StopInstalledProcessByPath" in source
    assert "-ErrorAction SilentlyContinue" in source
    assert "RemoveInstalledBackupTask()" in source
    assert 'Type: filesandordirs; Name: "{app}"' in source
    assert "farm data remains under its independent backup/recovery ownership" in source


def test_installer_provisions_six_hour_backup_task():
    source = ISS.read_text(encoding="utf-8-sig")
    assert "New-TimeSpan -Hours 6" in source


def test_ci_certifies_simplified_uninstall_and_six_hour_schedule():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    start = workflow.index("Certify simplified install and uninstall")
    active = workflow[start:workflow.index("Publish installer artifact", start)]
    assert "Certify simplified install and uninstall" in active
    assert "PT6H" in active
    assert "PRESERVEFARMDATA" not in active
    assert "keep-data uninstall" not in active
