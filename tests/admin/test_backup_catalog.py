from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from dairyos.admin import backup_catalog as catalog
from dairyos.data.database.backup import verify_backup_artifact


def dump(
    root: Path, name="DairyOS-Auto-test.dump", created="2026-09-08T12:00:00Z"
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / name
    path.write_bytes(b"test archive")
    path.with_suffix(".dump.json").write_text(
        json.dumps(
            {
                "file": path.name,
                "archive_verified": True,
                "created_at": created,
                "kind": "ROLLING_PRIMARY",
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "size_bytes": path.stat().st_size,
            }
        )
    )
    return path


def snapshot(root: Path) -> Path:
    (root / "files/storage").mkdir(parents=True)
    data = root / "files/storage/example.json"
    data.write_text("[]")
    archive = root / "database.dump"
    archive.write_bytes(b"test archive")
    (root / "backup.json").write_text(
        json.dumps(
            {
                "database_backup": archive.name,
                "database_backup_archive_verified": True,
                "database_backup_sha256": hashlib.sha256(
                    archive.read_bytes()
                ).hexdigest(),
                "created_at": "2026-09-08T10:00:00Z",
                "label": "admin",
                "files": [
                    {
                        "path": "storage/example.json",
                        "sha256": hashlib.sha256(data.read_bytes()).hexdigest(),
                    }
                ],
            }
        )
    )
    return root


@pytest.fixture
def archive_check(monkeypatch):
    calls = []

    def verify(path):
        calls.append(Path(path))
        return verify_backup_artifact(path)

    monkeypatch.setattr(catalog, "verify_backup_archive", verify)
    return calls


def test_discovers_both_types_and_mirrors_without_duplicates_newest_first(
    tmp_path, archive_check
):
    root = tmp_path / "backups"
    full = snapshot(root / "admin")
    primary = dump(root / "automatic/primary")
    mirror = dump(tmp_path / "mirror/automatic", created="2026-09-08T11:00:00Z")
    rows, problems = catalog.discover_verified_backups(
        tmp_path, roots=[root, root / "automatic", tmp_path / "mirror"]
    )
    assert [x.path for x in rows] == [primary, mirror, full]
    assert [x.kind for x in rows] == ["database", "database", "snapshot"]
    assert not problems
    assert len(archive_check) == 3


def test_rechecks_tampered_dump_and_snapshot_and_ignores_staging(
    tmp_path, archive_check
):
    full = snapshot(tmp_path / "backups/admin")
    archive = dump(tmp_path / "backups/automatic")
    snapshot(tmp_path / "backups/.staging/unfinished")
    (full / "files/storage/example.json").write_text("changed")
    archive.write_bytes(b"changed")
    rows, problems = catalog.discover_verified_backups(
        tmp_path, roots=[tmp_path / "backups"]
    )
    assert rows == []
    assert len(problems) == 2


@pytest.mark.parametrize("relative", ["../outside", "/outside", "C:/outside"])
def test_manifest_paths_must_stay_inside_snapshot(tmp_path, archive_check, relative):
    full = snapshot(tmp_path / "full")
    manifest = json.loads((full / "backup.json").read_text())
    manifest["files"][0]["path"] = relative
    (full / "backup.json").write_text(json.dumps(manifest))
    rows, problems = catalog.discover_verified_backups(tmp_path, roots=[full])
    assert not rows
    assert len(problems) == 1


def test_bad_or_unverified_metadata_is_not_offered(tmp_path, archive_check):
    path = dump(tmp_path / "automatic")
    path.with_suffix(".dump.json").write_text('{"archive_verified":false}')
    rows, problems = catalog.discover_verified_backups(tmp_path, roots=[tmp_path])
    assert not rows and len(problems) == 1


def test_catalog_honors_configured_external_roots(tmp_path, monkeypatch):
    monkeypatch.setenv("DAIRYOS_BACKUP_MIRROR_ROOT", str(tmp_path / "external"))
    monkeypatch.setenv("DAIRYOS_RECOVERY_ROOT", str(tmp_path / "recovery"))
    roots = catalog.backup_search_roots(tmp_path / "farm")
    assert tmp_path / "external" in roots
    assert tmp_path / "recovery" in roots


def test_installer_owns_explicit_recovery_choice_without_standalone_admin():
    source = Path(__file__).parents[2] / "tools/windows-desktop/DairyOS-Installer.iss"
    text = source.read_text()
    assert 'Parameters: "--restore-mode"' not in text
    assert "DairyOS-Admin.exe" not in text
    assert "Restore from a verified backup" in text
    assert "Create a separate empty farm (preserve existing data)" in text
    assert "ScanKnownBackupRoots" in text
    assert "StageInstallationChoice" in text


@pytest.mark.parametrize("inventory", [None, {}, "files", [None], ["file"], [123]])
def test_malformed_inventory_is_rejected(tmp_path, archive_check, inventory):
    full = snapshot(tmp_path / "full")
    manifest = json.loads((full / "backup.json").read_text())
    manifest["files"] = inventory
    (full / "backup.json").write_text(json.dumps(manifest))
    rows, problems = catalog.discover_verified_backups(tmp_path, roots=[full])
    assert rows == []
    assert len(problems) == 1


def test_unmanifested_file_is_rejected(tmp_path, archive_check):
    full = snapshot(tmp_path / "full")
    (full / "files/storage/unlisted.json").write_text("unexpected")
    with pytest.raises(catalog.LifecycleError, match="unmanifested"):
        catalog.verify_restore_candidate(full)


def test_duplicate_inventory_is_rejected(tmp_path, archive_check):
    full = snapshot(tmp_path / "full")
    manifest = json.loads((full / "backup.json").read_text())
    manifest["files"] *= 2
    (full / "backup.json").write_text(json.dumps(manifest))
    with pytest.raises(catalog.LifecycleError, match="duplicate"):
        catalog.verify_restore_candidate(full)


def test_explicit_staging_archive_is_rejected(tmp_path, archive_check):
    archive = dump(tmp_path / ".staging")
    with pytest.raises(catalog.LifecycleError, match="staging"):
        catalog.verify_restore_candidate(archive)


def test_snapshot_without_database_checksum_is_not_verified(tmp_path, archive_check):
    full = snapshot(tmp_path / "full")
    manifest = json.loads((full / "backup.json").read_text())
    del manifest["database_backup_sha256"]
    (full / "backup.json").write_text(json.dumps(manifest))
    with pytest.raises(catalog.LifecycleError, match="checksum"):
        catalog.verify_restore_candidate(full)
