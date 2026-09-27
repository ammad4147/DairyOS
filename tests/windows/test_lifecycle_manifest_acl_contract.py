import json
from pathlib import Path

from dairyos.lifecycle import manager as lifecycle_manager

ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "src" / "dairyos/lifecycle/manager.py"
ISS = ROOT / "tools" / "windows-desktop" / "DairyOS-Installer.iss"
WORKFLOW = ROOT / ".github" / "workflows" / "installer-windows.yml"


def test_existing_lifecycle_json_uses_acl_preserving_atomic_replace():
    source = MANAGER.read_text(encoding="utf-8")

    assert "def _replace_file_preserving_acl(" in source
    assert 'if os.name != "nt" or not path.exists():' in source
    assert "ReplaceFileW" in source

    writer_start = source.index("def _write_json_atomic(")
    writer = source[writer_start:]

    assert "_replace_file_preserving_acl(temporary, path)" in writer


def test_atomic_json_writer_round_trips_existing_file(tmp_path):
    path = tmp_path / "lifecycle.json"

    lifecycle_manager._write_json_atomic(path, {"generation": 1})
    lifecycle_manager._write_json_atomic(path, {"generation": 2})

    assert json.loads(path.read_text(encoding="utf-8")) == {
        "generation": 2
    }


def test_installer_grants_modify_only_to_lifecycle_manifest():
    source = ISS.read_text(encoding="utf-8")

    assert "procedure ProvisionLifecycleManifestAcl();" in source
    assert "LifecyclePath := DairyOSDataRoot('') + '\\lifecycle.json';" in source
    assert "/grant:r *S-1-5-32-545:(M)" in source

    start = source.index("procedure ProvisionLifecycleManifestAcl();")
    end = source.index(
        "procedure ProvisionBackupTreeAcl();",
        start,
    )
    block = source[start:end]

    assert "/T" not in block
    assert "security.json" not in block
    assert "postgres\\data" not in block

    lifecycle = source.index("    ProvisionLifecycleState();")
    lifecycle_acl = source.index("    ProvisionLifecycleManifestAcl();")
    backup_acl = source.index("    ProvisionBackupTreeAcl();")
    backup_task = source.index("    ProvisionAutomaticBackupTask();")

    assert lifecycle < lifecycle_acl < backup_acl < backup_task



def test_installer_does_not_provision_retired_installation_choice_acl():
    source = ISS.read_text(encoding="utf-8-sig")

    assert "procedure ProvisionInstallationChoiceAcl();" not in source
    assert "ProvisionInstallationChoiceAcl();" not in source
    assert "pending-installation-choice.json" not in source
    assert "StageInstallationChoice" not in source

    # Durable lifecycle/storage authorities remain provisioned.
    assert "ProvisionLifecycleManifestAcl();" in source
    assert "ProvisionStorageTreeAcl();" in source
    assert "ProvisionBackupTreeAcl();" in source


def _active_certification() -> str:
    workflow = WORKFLOW.read_text(encoding="utf-8-sig")
    start = workflow.index("- name: Certify simplified install and uninstall")
    return workflow[start:workflow.index("- name: Publish installer artifact", start)]


def test_installer_ci_certifies_installed_lifecycle_acl():
    active = _active_certification()

    assert "$usersSid = 'S-1-5-32-545'" in active
    assert "Assert-UsersCanModify $lifecycleJson 'Installed lifecycle.json'" in active
    assert "LIFECYCLE MANIFEST ACL CERTIFICATION: PASS" in active


def test_backup_acl_is_scoped_separately_from_lifecycle_acl():
    source = ISS.read_text(encoding="utf-8")
    start = source.index("procedure ProvisionBackupTreeAcl();")
    end = source.index("procedure ProvisionAutomaticBackupTask();", start)
    block = source[start:end]

    assert "BackupPath := DairyOSDataRoot('') + '\\backups';" in block
    assert "*S-1-5-32-545:(OI)(CI)(M)" in block
    assert "/T /C" in block

    # Verify scope by path targets/commands, not explanatory prose.
    assert "DairyOSDataRoot('') + '\\postgres" not in block
    assert "DairyOSDataRoot('') + '\\security" not in block
    assert "security.json" not in block

def test_windows_ci_retires_installation_choice_and_certifies_canonical_collision():
    workflow = WORKFLOW.read_text(encoding="utf-8-sig")

    for token in (
        "pending-installation-choice",
        "$pendingChoicePath",
        "$pendingChoiceAllowsModify",
        "INSTALLATION CHOICE ACL CERTIFICATION",
        "--choice-mode",
        "--lifecycle-choice",
        "--backup-path",
        "Continue with Existing Farm",
        "Restore to Verified Backup",
        # Retired behaviour: uninstall never deletes farm data any more.
        "NO-PRESERVATION CERTIFICATION",
    ):
        assert token not in workflow

    # Certification steps must run; a disabled step only pretends to certify.
    assert "if: ${{ false }}" not in workflow

    active = _active_certification()
    for marker in (
        "LIFECYCLE MANIFEST ACL CERTIFICATION: PASS",
        "OPERATIONAL STORAGE ACL CERTIFICATION: PASS",
        "BACKUP TREE ACL CERTIFICATION: PASS",
        "INSTALLED COMPONENTS AND MANIFEST BINDING: PASS",
        "STALE-ENVIRONMENT INSTALLED PREFLIGHT: PASS",
        "INSTALLED SCHEDULED BACKUP EXECUTION: PASS",
        "CANONICAL DATA COLLISION FAIL-CLOSED CERTIFICATION: PASS",
    ):
        assert marker in active, marker
