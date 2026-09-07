"""Strict lifecycle snapshot restoration."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from dairyos.data.database.backup import restore_backup, verify_backup_archive

from .manager import LifecycleError, LifecycleManager


_DATABASE_ROOT_NAMES = {"postgres", "postgresql"}


def restore_snapshot(manager: LifecycleManager, backup: str | Path) -> None:
    """Restore a verified lifecycle snapshot without destructive-first mutation.

    PostgreSQL is restored only from the logical database dump. Physical
    PostgreSQL data directories are never deleted or copied by this routine.
    A verified pre-restore rollback artifact is created before the target dump
    or non-database files are changed.
    """

    backup_path = Path(backup).expanduser().resolve()
    manifest = _load_verified_manifest(backup_path)

    database_backup = manifest.get("database_backup")
    if not database_backup:
        raise LifecycleError(
            "DairyOS restore requires a verified PostgreSQL database dump."
        )
    if not manager.database_url:
        raise LifecycleError(
            "Backup contains a database dump but no database URL is configured."
        )

    dump_path = backup_path / str(database_backup)
    verify_backup_archive(dump_path)

    # Materialize the target file state completely before touching live state.
    with tempfile.TemporaryDirectory(prefix="dairyos-restore-stage-") as temporary:
        staged_root = Path(temporary) / "files"
        staged_root.mkdir(parents=True, exist_ok=True)
        _stage_non_database_files(
            backup_path / "files",
            manifest.get("files") or [],
            staged_root,
        )

        rollback = manager.backup(
            label="pre-restore-rollback",
            require_database=True,
        )
        rollback_manifest = _load_verified_manifest(rollback)
        rollback_dump = rollback / str(rollback_manifest["database_backup"])
        verify_backup_archive(rollback_dump)

        database_changed = False
        files_changed = False
        try:
            restore_backup(manager.database_url, dump_path)
            database_changed = True
            _replace_non_database_files(manager.data_root, staged_root)
            files_changed = True
            manager.validate(require_database=True)
        except Exception as exc:
            rollback_errors: list[str] = []

            if database_changed:
                try:
                    restore_backup(manager.database_url, rollback_dump)
                except Exception as rollback_exc:  # pragma: no cover - catastrophic path
                    rollback_errors.append(
                        f"database rollback failed: {rollback_exc}"
                    )

            if files_changed or database_changed:
                try:
                    rollback_stage = Path(temporary) / "rollback-files"
                    rollback_stage.mkdir(parents=True, exist_ok=True)
                    _stage_non_database_files(
                        rollback / "files",
                        rollback_manifest.get("files") or [],
                        rollback_stage,
                    )
                    _replace_non_database_files(manager.data_root, rollback_stage)
                except Exception as rollback_exc:  # pragma: no cover - catastrophic path
                    rollback_errors.append(
                        f"file rollback failed: {rollback_exc}"
                    )

            if rollback_errors:
                raise LifecycleError(
                    "Restore failed and automatic rollback was incomplete: "
                    + "; ".join(rollback_errors)
                ) from exc

            raise LifecycleError(
                f"Restore failed; pre-restore state was restored: {exc}"
            ) from exc


def _load_verified_manifest(backup_path: Path) -> dict[str, object]:
    manifest_path = backup_path / "backup.json"
    files_root = backup_path / "files"

    if not manifest_path.is_file() or not files_root.is_dir():
        raise LifecycleError(f"Invalid DairyOS backup: {backup_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest.get("files") or []

    for entry in entries:
        relative = Path(str(entry["path"]))
        if not relative.parts:
            raise LifecycleError("Backup contains an empty file path.")
        source = files_root / relative
        if not source.is_file():
            raise LifecycleError(f"Backup file is missing: {relative}")
        expected_hash = str(entry.get("sha256") or "")
        if expected_hash and _sha256(source) != expected_hash:
            raise LifecycleError(f"Backup integrity check failed: {relative}")

    database_backup = manifest.get("database_backup")
    if database_backup:
        dump_path = backup_path / str(database_backup)
        if not dump_path.is_file():
            raise LifecycleError(
                f"PostgreSQL backup artifact is missing: {dump_path}"
            )

    return manifest


def _stage_non_database_files(
    files_root: Path,
    entries: list[dict[str, object]] | tuple[dict[str, object], ...],
    staged_root: Path,
) -> None:
    for entry in entries:
        relative = Path(str(entry["path"]))
        if relative.parts and relative.parts[0].lower() in _DATABASE_ROOT_NAMES:
            continue
        source = files_root / relative
        destination = staged_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _replace_non_database_files(data_root: Path, staged_root: Path) -> None:
    """Replace only non-database persistent state.

    Backups and PostgreSQL roots are lifecycle authorities of their own and are
    never removed as part of file promotion.
    """

    data_root.mkdir(parents=True, exist_ok=True)
    preserved = {"backups", *_DATABASE_ROOT_NAMES}

    for child in data_root.iterdir():
        if child.name.lower() in preserved:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    for source in staged_root.rglob("*"):
        if not source.is_file():
            continue
        relative = source.relative_to(staged_root)
        destination = data_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
