import json
from pathlib import Path

from dairyos.lifecycle import manager as lifecycle_manager


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "src" / "dairyos" / "lifecycle" / "manager.py"
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
    assert "LifecyclePath := DairyOSDataRoot() + '\\lifecycle.json';" in source
    assert "/grant:r *S-1-5-32-545:(M)" in source

    start = source.index("procedure ProvisionLifecycleManifestAcl();")
    end = source.index(
        "procedure ProvisionAutomaticBackupTask();",
        start,
    )
    block = source[start:end]

    assert "/T" not in block
    assert "security.json" not in block
    assert "postgres\\data" not in block

    lifecycle = source.index("    ProvisionLifecycleState();")
    acl = source.index("    ProvisionLifecycleManifestAcl();")
    backup = source.index("    ProvisionAutomaticBackupTask();")

    assert lifecycle < acl < backup


def test_installer_ci_certifies_installed_lifecycle_acl():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert '$usersSid = "S-1-5-32-545"' in source
    assert "LIFECYCLE MANIFEST ACL CERTIFICATION: PASS" in source
    assert "Installed lifecycle.json is not modifiable" in source

def test_backup_acl_is_scoped_separately_from_lifecycle_acl():
    source = ISS.read_text(encoding="utf-8")
    start = source.index("procedure ProvisionBackupTreeAcl();")
    end = source.index("procedure ProvisionAutomaticBackupTask();", start)
    block = source[start:end]
    assert "DairyOSDataRoot() + '\\backups'" in block
    assert "(OI)(CI)(M)" in block
    assert "postgres" not in block.lower()
    assert "security" not in block.lower()
