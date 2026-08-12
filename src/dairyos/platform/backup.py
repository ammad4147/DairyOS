"""Database backup and restore primitives for DairyOS disaster recovery.

The application database is the authoritative persistence boundary for
operational records. This module deliberately shells out to PostgreSQL's
native pg_dump/pg_restore tools rather than attempting to reimplement a
logical database backup in Python.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.engine import make_url


class BackupError(RuntimeError):
    """Raised when a backup or restore operation cannot be completed."""


def _database_url() -> str:
    value = os.getenv("DAIRYOS_DATABASE_URL")
    if value:
        return value
    from dairyos.data.database.session import DATABASE_URL

    return DATABASE_URL


def _pg_environment(database_url: str) -> dict[str, str]:
    url = make_url(database_url)
    env = os.environ.copy()
    if url.password is not None:
        env["PGPASSWORD"] = url.password
    return env


def _require_tool(name: str) -> str:
    executable = shutil.which(name)
    if not executable:
        raise BackupError(
            f"Required PostgreSQL tool {name!r} was not found on PATH. "
            "Install the PostgreSQL client tools before running disaster recovery."
        )
    return executable


def _checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_backup(destination: str | Path) -> Path:
    """Create a verified PostgreSQL custom-format backup and manifest."""
    pg_dump = _require_tool("pg_dump")
    database_url = _database_url()
    url = make_url(database_url)
    target = Path(destination).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    dump_path = target / "dairyos.dump"

    command = [pg_dump, "--format=custom", "--no-owner", "--file", str(dump_path), database_url]
    completed = subprocess.run(
        command,
        env=_pg_environment(database_url),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        dump_path.unlink(missing_ok=True)
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown pg_dump error"
        raise BackupError(f"pg_dump failed: {detail}")

    if not dump_path.exists() or dump_path.stat().st_size == 0:
        raise BackupError("pg_dump completed without producing a non-empty backup.")

    manifest = {
        "format": "dairyos-postgresql-custom",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "database": url.database,
        "host": url.host,
        "port": url.port,
        "backup_file": dump_path.name,
        "sha256": _checksum(dump_path),
        "size_bytes": dump_path.stat().st_size,
    }
    manifest_path = target / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def restore_backup(backup_directory: str | Path) -> None:
    """Verify a backup manifest and restore it into the configured database."""
    pg_restore = _require_tool("pg_restore")
    source = Path(backup_directory).expanduser().resolve()
    manifest_path = source / "manifest.json"
    if not manifest_path.exists():
        raise BackupError(f"Backup manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dump_path = source / str(manifest.get("backup_file", ""))
    if not dump_path.exists():
        raise BackupError(f"Backup payload not found: {dump_path}")
    expected = str(manifest.get("sha256", ""))
    actual = _checksum(dump_path)
    if not expected or expected != actual:
        raise BackupError("Backup checksum verification failed; refusing to restore.")

    database_url = _database_url()
    command = [
        pg_restore,
        "--clean",
        "--if-exists",
        "--no-owner",
        "--dbname",
        database_url,
        str(dump_path),
    ]
    completed = subprocess.run(
        command,
        env=_pg_environment(database_url),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown pg_restore error"
        raise BackupError(f"pg_restore failed: {detail}")
