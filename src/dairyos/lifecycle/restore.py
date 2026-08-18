"""Strict lifecycle snapshot restoration."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from dairyos.data.database.backup import restore_backup

from .manager import LifecycleError, LifecycleManager


def restore_snapshot(manager: LifecycleManager, backup: str | Path) -> None:
    """Restore a snapshot exactly, removing files not present in the snapshot."""

    backup_path = Path(backup).expanduser().resolve()
    manifest_path = backup_path / "backup.json"
    files_root = backup_path / "files"

    if not manifest_path.is_file() or not files_root.is_dir():
        raise LifecycleError(f"Invalid DairyOS backup: {backup_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest.get("files") or []

    for entry in entries:
        relative = Path(str(entry["path"]))
        source = files_root / relative
        if not source.is_file():
            raise LifecycleError(f"Backup file is missing: {relative}")
        expected_hash = str(entry.get("sha256") or "")
        if expected_hash and _sha256(source) != expected_hash:
            raise LifecycleError(f"Backup integrity check failed: {relative}")

    manager.data_root.mkdir(parents=True, exist_ok=True)
    for child in manager.data_root.iterdir():
        if child.name == "backups":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    for entry in entries:
        relative = Path(str(entry["path"]))
        source = files_root / relative
        destination = manager.data_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    database_backup = manifest.get("database_backup")
    if database_backup:
        if not manager.database_url:
            raise LifecycleError("Backup contains a database dump but no database URL is configured")
        restore_backup(manager.database_url, backup_path / str(database_backup))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
