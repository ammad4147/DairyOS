from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

from sqlalchemy.engine import make_url


COMMAND_TIMEOUT_SECONDS = 120


class PostgreSQLBackupError(RuntimeError):
    """Raised when a PostgreSQL backup or restore operation fails."""


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise PostgreSQLBackupError(
            f"Required PostgreSQL utility {name!r} was not found on PATH."
        )
    return path


def _connection_args(database_url: str) -> tuple[list[str], dict[str, str]]:
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql":
        raise PostgreSQLBackupError("DairyOS backup requires a PostgreSQL database URL.")

    args: list[str] = []
    if url.host:
        args += ["--host", url.host]
    if url.port:
        args += ["--port", str(url.port)]
    if url.username:
        args += ["--username", url.username]
    if url.database:
        args += ["--dbname", url.database]

    env = os.environ.copy()
    if url.password is not None:
        env["PGPASSWORD"] = url.password
    return args, env


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_postgresql_command(command: list[str], env: dict[str, str], operation: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise PostgreSQLBackupError(
            f"{operation} timed out after {COMMAND_TIMEOUT_SECONDS} seconds."
        ) from exc


def create_backup(database_url: str, destination: str | Path) -> Path:
    """Create a compressed, self-contained PostgreSQL custom-format backup."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    args, env = _connection_args(database_url)
    command = [
        _tool("pg_dump"),
        "--format=custom",
        "--no-owner",
        *args,
        "--file",
        str(destination),
    ]
    completed = _run_postgresql_command(command, env, "pg_dump")
    if completed.returncode != 0:
        destination.unlink(missing_ok=True)
        raise PostgreSQLBackupError(completed.stderr.strip() or "pg_dump failed")
    if not destination.is_file() or destination.stat().st_size == 0:
        raise PostgreSQLBackupError("pg_dump completed without producing a backup artifact.")
    return destination


def restore_backup(database_url: str, backup: str | Path) -> None:
    """Restore a custom-format backup into an existing PostgreSQL database."""
    backup = Path(backup)
    if not backup.is_file() or backup.stat().st_size == 0:
        raise PostgreSQLBackupError(f"Backup artifact does not exist or is empty: {backup}")
    args, env = _connection_args(database_url)
    command = [
        _tool("pg_restore"),
        "--exit-on-error",
        "--no-owner",
        "--clean",
        "--if-exists",
        *args,
        str(backup),
    ]
    completed = _run_postgresql_command(command, env, "pg_restore")
    if completed.returncode != 0:
        raise PostgreSQLBackupError(completed.stderr.strip() or "pg_restore failed")


def verify_backup_artifact(backup: str | Path) -> dict[str, int | str]:
    """Verify and return auditable PostgreSQL backup metadata."""
    path = Path(backup)
    if not path.is_file():
        raise PostgreSQLBackupError(f"Backup artifact not found: {path}")
    size = path.stat().st_size
    if size <= 0:
        raise PostgreSQLBackupError(f"Backup artifact is empty: {path}")
    return {"path": str(path), "size_bytes": size, "sha256": _sha256(path)}


def verify_backup_checksum(backup: str | Path, expected_sha256: str) -> dict[str, int | str]:
    """Verify a PostgreSQL backup against an independently recorded SHA-256."""
    metadata = verify_backup_artifact(backup)
    actual = str(metadata["sha256"])
    expected = expected_sha256.strip().lower()
    if actual != expected:
        raise PostgreSQLBackupError(
            f"Backup SHA-256 mismatch for {metadata['path']}: expected {expected}, got {actual}"
        )
    return metadata
