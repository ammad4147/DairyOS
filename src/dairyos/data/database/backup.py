from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

from sqlalchemy.engine import make_url


COMMAND_TIMEOUT_SECONDS = 120
LOCK_WAIT_TIMEOUT = "15s"


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
    password = os.getenv("DAIRYOS_DB_PASSWORD") or url.password
    if password is not None:
        env["PGPASSWORD"] = password
    return args, env


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_postgresql_command(
    command: list[str],
    env: dict[str, str],
    operation: str,
) -> subprocess.CompletedProcess[str]:
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
        f"--lock-wait-timeout={LOCK_WAIT_TIMEOUT}",
        "--verbose",
        *args,
        "--file",
        str(destination),
    ]
    completed = _run_postgresql_command(command, env, "pg_dump")
    if completed.returncode != 0:
        destination.unlink(missing_ok=True)
        detail = completed.stderr.strip() or completed.stdout.strip() or "pg_dump failed"
        raise PostgreSQLBackupError(detail)
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
        "--verbose",
        *args,
        str(backup),
    ]
    completed = _run_postgresql_command(command, env, "pg_restore")
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "pg_restore failed"
        raise PostgreSQLBackupError(detail)


def verify_backup_artifact(backup: str | Path) -> dict[str, int | str]:
    """Verify and return auditable PostgreSQL backup metadata."""
    path = Path(backup)
    if not path.is_file():
        raise PostgreSQLBackupError(f"Backup artifact not found: {path}")
    size = path.stat().st_size
    if size <= 0:
        raise PostgreSQLBackupError(f"Backup artifact is empty: {path}")
    return {"path": str(path), "size_bytes": size, "sha256": _sha256(path)}


def verify_backup_archive(backup: str | Path) -> dict[str, int | str]:
    """Verify a custom-format dump can be parsed by PostgreSQL tooling.

    A checksum proves that a file did not change after it was created.  This
    additional check asks ``pg_restore`` to read the archive catalog, catching
    empty, truncated, or structurally invalid dump files before DairyOS marks a
    scheduled backup as healthy.
    """

    metadata = verify_backup_artifact(backup)
    path = Path(backup)
    completed = _run_postgresql_command(
        [_tool("pg_restore"), "--list", str(path)],
        os.environ.copy(),
        "pg_restore archive verification",
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "pg_restore --list failed"
        raise PostgreSQLBackupError(
            f"PostgreSQL backup archive verification failed for {path}: {detail}"
        )
    if not completed.stdout.strip():
        raise PostgreSQLBackupError(
            f"PostgreSQL backup archive catalog is unexpectedly empty: {path}"
        )
    metadata["archive_verified"] = "true"
    return metadata


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
