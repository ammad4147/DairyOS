from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ISS = ROOT / "tools" / "windows-desktop" / "DairyOS-Installer.iss"
WORKFLOW = ROOT / ".github" / "workflows" / "installer-windows.yml"


def test_installer_provisions_backup_task_elevated():
    source = ISS.read_text(encoding="utf-8")
    assert "procedure ProvisionAutomaticBackupTask();" in source
    assert "DairyOS-Automatic-Backup" in source
    assert "/SC HOURLY /MO 6 /ST 00:00 /RL LIMITED" in source
    assert "CurStep = ssPostInstall" in source
    assert "Setup cannot continue safely" in source


def test_installer_ci_verifies_task_before_app_start():
    source = WORKFLOW.read_text(encoding="utf-8")
    query = source.index('schtasks.exe /Query /TN "DairyOS-Automatic-Backup"')
    preflight = source.index("$preflight = Start-Process -FilePath $installedExe")
    assert query < preflight


def test_installer_ci_verifies_task_action_and_executes_backup_worker():
    installer = ISS.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "'/TR \"' + BackupExe + '\"'" in installer
    assert "Automatic backup task points to the wrong executable" in workflow
    assert "Installed DairyOS backup worker failed with code" in workflow
    assert "backup-health.json" in workflow
