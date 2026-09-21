from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ISS = ROOT / "tools" / "windows-desktop" / "DairyOS-Installer.iss"
WORKFLOW = ROOT / ".github" / "workflows" / "installer-windows.yml"


def test_installer_provisions_backup_task_with_structured_action():
    source = ISS.read_text(encoding="utf-8")
    assert "procedure ProvisionAutomaticBackupTask();" in source
    assert "DairyOS-Automatic-Backup" in source
    assert "New-ScheduledTaskAction -Execute" in source
    assert "New-ScheduledTaskTrigger -Once" in source
    assert "New-TimeSpan -Hours 6" in source
    assert "Register-ScheduledTask" in source
    assert "-RunLevel Limited" in source
    assert "CurStep = ssPostInstall" in source
    assert "Setup cannot continue safely" in source
    start = source.index("procedure ProvisionAutomaticBackupTask();")
    end = source.index("procedure CurStepChanged", start)
    block = source[start:end]
    assert "schtasks.exe" not in block
    assert "/Create /F /TN" not in block


def test_installer_ci_verifies_structured_task_before_app_start():
    source = WORKFLOW.read_text(encoding="utf-8")
    structured = source.index('$task = Get-ScheduledTask -TaskName "DairyOS-Automatic-Backup"')
    preflight = source.index("$preflight = Start-Process -FilePath $installedExe")
    assert structured < preflight
    assert "$taskExecute" in source
    assert "$taskArguments" in source
    assert "AUTOMATIC BACKUP TASK STRUCTURED ACTION: PASS" in source


def test_installer_ci_executes_registered_scheduled_task_and_checks_health():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert 'Start-ScheduledTask -TaskName "DairyOS-Automatic-Backup"' in workflow
    assert 'Get-ScheduledTaskInfo -TaskName "DairyOS-Automatic-Backup"' in workflow
    assert "LastTaskResult" in workflow
    assert "backup-health.json" in workflow
    assert "INSTALLED SCHEDULED BACKUP EXECUTION: PASS" in workflow


def test_installer_provisions_modify_acl_only_for_mutable_backup_tree():
    source = ISS.read_text(encoding="utf-8")
    assert "procedure ProvisionBackupTreeAcl();" in source
    assert "BackupPath := DairyOSDataRoot('') + '\\backups';" in source
    assert "*S-1-5-32-545:(OI)(CI)(M)" in source
    assert "/T /C" in source

    start = source.index("procedure ProvisionBackupTreeAcl();")
    end = source.index("procedure ProvisionAutomaticBackupTask();", start)
    block = source[start:end]
    assert "postgres\\data" not in block
    assert "security.json" not in block

    lifecycle_acl = source.index("    ProvisionLifecycleManifestAcl();")
    backup_acl = source.index("    ProvisionBackupTreeAcl();")
    task = source.index("    ProvisionAutomaticBackupTask();")
    assert lifecycle_acl < backup_acl < task
