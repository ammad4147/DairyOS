import hashlib
import json
from pathlib import Path

import pytest

from dairyos.admin.service import _verify_backup_directory
from dairyos.lifecycle.manager import LifecycleError


def test_admin_backup_verification_accepts_matching_database_checksum(tmp_path: Path):
    backup = tmp_path / "backup"
    files = backup / "files"
    files.mkdir(parents=True)
    dump = backup / "database.dump"
    dump.write_bytes(b"database-backup")
    digest = hashlib.sha256(dump.read_bytes()).hexdigest()
    (files / "example.txt").write_text("ok", encoding="utf-8")
    file_digest = hashlib.sha256((files / "example.txt").read_bytes()).hexdigest()
    (backup / "backup.json").write_text(
        json.dumps(
            {
                "database_backup": "database.dump",
                "database_backup_sha256": digest,
                "files": [{"path": "example.txt", "sha256": file_digest}],
            }
        ),
        encoding="utf-8",
    )

    _verify_backup_directory(backup)


def test_admin_backup_verification_rejects_tampered_database_dump(tmp_path: Path):
    backup = tmp_path / "backup"
    backup.mkdir()
    dump = backup / "database.dump"
    dump.write_bytes(b"tampered")
    (backup / "backup.json").write_text(
        json.dumps(
            {
                "database_backup": "database.dump",
                "database_backup_sha256": hashlib.sha256(b"original").hexdigest(),
                "files": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(LifecycleError, match="PostgreSQL backup SHA-256"):
        _verify_backup_directory(backup)
