from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from dairyos.lifecycle.manager import LifecycleError
from dairyos.lifecycle.restore import restore_snapshot


class FakeManager:
    def __init__(self, data_root: Path, rollback_backup: Path):
        self.data_root = data_root
        self.database_url = "postgresql+psycopg://admin@example/dairyos"
        self.rollback_backup = rollback_backup
        self.backup_calls: list[tuple[str, bool]] = []
        self.validate_calls: list[bool] = []

    def backup(self, label="pre-change", *, require_database=False):
        self.backup_calls.append((label, require_database))
        return self.rollback_backup

    def validate(self, require_database=True):
        self.validate_calls.append(require_database)
        return {"valid": True}


def _write_backup(root: Path, files: dict[str, bytes]) -> Path:
    files_root = root / "files"
    files_root.mkdir(parents=True)
    entries = []
    for relative, payload in files.items():
        target = files_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        entries.append(
            {
                "path": relative.replace("\\", "/"),
                "size_bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )

    dump = root / "database.dump"
    dump.write_bytes(b"postgres-dump")
    (root / "backup.json").write_text(
        json.dumps(
            {
                "files": entries,
                "database_backup": "database.dump",
                "database_backup_archive_verified": True,
            }
        ),
        encoding="utf-8",
    )
    return root


def test_restore_database_failure_leaves_live_files_and_postgres_untouched(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    live = tmp_path / "live"
    (live / "storage").mkdir(parents=True)
    (live / "storage" / "live.txt").write_text("live", encoding="utf-8")
    (live / "postgres" / "data").mkdir(parents=True)
    (live / "postgres" / "data" / "identity").write_text("keep", encoding="utf-8")

    target = _write_backup(
        tmp_path / "target",
        {"storage/target.txt": b"target"},
    )
    rollback = _write_backup(
        tmp_path / "rollback",
        {"storage/live.txt": b"live"},
    )
    manager = FakeManager(live, rollback)

    monkeypatch.setattr(
        "dairyos.lifecycle.restore.verify_backup_archive",
        lambda path: {"archive_verified": "true"},
    )
    monkeypatch.setattr(
        "dairyos.lifecycle.restore.restore_backup",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("restore exploded")),
    )

    with pytest.raises(LifecycleError, match="pre-restore state was restored"):
        restore_snapshot(manager, target)

    assert (live / "storage" / "live.txt").read_text(encoding="utf-8") == "live"
    assert not (live / "storage" / "target.txt").exists()
    assert (live / "postgres" / "data" / "identity").read_text(
        encoding="utf-8"
    ) == "keep"
    assert manager.backup_calls == [("pre-restore-rollback", True)]


def test_restore_never_promotes_or_deletes_physical_postgres_trees(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    live = tmp_path / "live"
    (live / "storage").mkdir(parents=True)
    (live / "storage" / "live.txt").write_text("live", encoding="utf-8")
    (live / "postgres" / "data").mkdir(parents=True)
    (live / "postgres" / "data" / "identity").write_text("keep", encoding="utf-8")
    (live / "postgresql" / "data").mkdir(parents=True)
    (live / "postgresql" / "data" / "stray").write_text("preserve", encoding="utf-8")

    target = _write_backup(
        tmp_path / "target",
        {
            "storage/target.txt": b"target",
            "postgres/data/replacement": b"must-not-promote",
            "postgresql/data/replacement": b"must-not-promote",
        },
    )
    rollback = _write_backup(
        tmp_path / "rollback",
        {"storage/live.txt": b"live"},
    )
    manager = FakeManager(live, rollback)

    monkeypatch.setattr(
        "dairyos.lifecycle.restore.verify_backup_archive",
        lambda path: {"archive_verified": "true"},
    )
    restored: list[Path] = []
    monkeypatch.setattr(
        "dairyos.lifecycle.restore.restore_backup",
        lambda _url, path: restored.append(Path(path)),
    )

    restore_snapshot(manager, target)

    assert not (live / "storage" / "live.txt").exists()
    assert (live / "storage" / "target.txt").read_text(encoding="utf-8") == "target"
    assert (live / "postgres" / "data" / "identity").read_text(
        encoding="utf-8"
    ) == "keep"
    assert not (live / "postgres" / "data" / "replacement").exists()
    assert (live / "postgresql" / "data" / "stray").read_text(
        encoding="utf-8"
    ) == "preserve"
    assert not (live / "postgresql" / "data" / "replacement").exists()
    assert restored == [target / "database.dump"]
    assert manager.validate_calls == [True]


def test_partial_file_promotion_failure_restores_pre_restore_state(
    tmp_path, monkeypatch
):
    from dairyos.lifecycle import restore

    live = tmp_path / "live"
    (live / "storage").mkdir(parents=True)
    (live / "storage/live.txt").write_text("live")
    target = _write_backup(tmp_path / "target", {"storage/target.txt": b"target"})
    rollback = _write_backup(tmp_path / "rollback", {"storage/live.txt": b"live"})
    manager = FakeManager(live, rollback)
    restored = []
    monkeypatch.setattr(restore, "verify_backup_archive", lambda path: {})
    monkeypatch.setattr(
        restore, "restore_backup", lambda url, path: restored.append(path)
    )
    promote = restore._replace_non_database_files
    calls = 0

    def fail_after_mutation(root, staged):
        nonlocal calls
        calls += 1
        if calls == 1:
            (root / "storage/live.txt").unlink()
            (root / "storage/partial.txt").write_text("partial")
            raise OSError("partial promotion")
        promote(root, staged)

    monkeypatch.setattr(restore, "_replace_non_database_files", fail_after_mutation)
    with pytest.raises(LifecycleError, match="pre-restore state was restored"):
        restore_snapshot(manager, target)
    assert restored == [target / "database.dump", rollback / "database.dump"]
    assert (live / "storage/live.txt").read_text() == "live"
    assert not (live / "storage/partial.txt").exists()
    assert calls == 2
