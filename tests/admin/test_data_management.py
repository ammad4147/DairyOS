from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from dairyos.admin import data_management as dm


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _minimal_package(root: Path) -> Path:
    root.mkdir()
    database = root / dm.PACKAGE_DATABASE_FILENAME
    database.write_bytes(b"postgres-dump")
    metadata = root / dm.PACKAGE_METADATA_FILENAME
    metadata.write_text(json.dumps({
        "format_version": dm.PACKAGE_FORMAT_VERSION,
        "farm_instance_id": "farm-test",
        "dairyos_version": "test",
        "semantic_fingerprint": {},
    }), encoding="utf-8")
    manifest = {
        "format_version": dm.PACKAGE_FORMAT_VERSION,
        "files": {
            dm.PACKAGE_DATABASE_FILENAME: _sha(database),
            dm.PACKAGE_METADATA_FILENAME: _sha(metadata),
        },
    }
    (root / dm.PACKAGE_MANIFEST_FILENAME).write_text(json.dumps(manifest), encoding="utf-8")
    return root


def test_validate_package_accepts_verified_members(tmp_path, monkeypatch):
    package = _minimal_package(tmp_path / "farm.dairypkg")
    monkeypatch.setattr(dm, "verify_backup_archive", lambda _path: {"archive_verified": "true"})
    result = dm.validate_package(package)
    assert result["valid"] is True
    assert result["farm_instance_id"] == "farm-test"


def test_validate_package_rejects_manifest_path_traversal(tmp_path, monkeypatch):
    package = _minimal_package(tmp_path / "farm.dairypkg")
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    manifest_path = package / dm.PACKAGE_MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"]["../outside.txt"] = _sha(outside)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(dm, "verify_backup_archive", lambda _path: {"archive_verified": "true"})
    with pytest.raises(dm.DataManagementError, match="unsafe path"):
        dm.validate_package(package)


def test_validate_package_rejects_corrupt_metadata_cleanly(tmp_path, monkeypatch):
    package = _minimal_package(tmp_path / "farm.dairypkg")
    metadata = package / dm.PACKAGE_METADATA_FILENAME
    metadata.write_text("{not-json", encoding="utf-8")
    manifest_path = package / dm.PACKAGE_MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][dm.PACKAGE_METADATA_FILENAME] = _sha(metadata)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(dm, "verify_backup_archive", lambda _path: {"archive_verified": "true"})
    with pytest.raises(dm.DataManagementError, match="metadata is corrupt"):
        dm.validate_package(package)


def test_dairyos_version_comes_from_package_metadata(monkeypatch):
    monkeypatch.setattr(dm, "package_version", lambda name: "9.8.7")
    assert dm._dairyos_version() == "9.8.7"
