"""Periodic proof that DairyOS backups can be restored, not merely parsed."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from dairyos.data.database.automatic_backups import backup_health_path, read_backup_health
from dairyos.data.database.backup import PostgreSQLBackupError, restore_backup, verify_backup_archive
from dairyos.platform import paths


RESTORE_VERIFY_INTERVAL = timedelta(days=7)


class RestoreVerificationError(RuntimeError):
    """Raised when a scheduled recovery proof cannot be completed."""


def _utc_now(now: datetime | None = None) -> datetime:
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse_time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def restore_verification_due(
    data_root: Path | None = None,
    *,
    now: datetime | None = None,
) -> bool:
    health = read_backup_health(data_root)
    last = _parse_time(health.get("last_restore_verification"))
    if last is None:
        return True
    return _utc_now(now) - last >= RESTORE_VERIFY_INTERVAL


def _write_health(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def verify_latest_backup_restore(
    admin_database_url: str,
    *,
    data_root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, object] | None:
    """Restore the latest verified dump into a disposable database and drop it.

    The caller must supply the transient migration/admin URL.  The function is
    therefore intended for the packaged startup security boundary, never the
    normal application process or read-only backup worker.
    """

    root = (data_root or paths.data_root(create=True)).resolve()
    health_path = backup_health_path(root)
    health = dict(read_backup_health(root))
    primary_value = health.get("primary")
    if not isinstance(primary_value, str) or not primary_value.strip():
        return None

    backup = Path(primary_value)
    if not backup.is_file():
        raise RestoreVerificationError(f"Latest DairyOS backup is missing: {backup}")

    try:
        verify_backup_archive(backup)
    except PostgreSQLBackupError as exc:
        raise RestoreVerificationError(str(exc)) from exc

    timestamp = _utc_now(now)
    scratch_name = f"dairyos_restore_verify_{timestamp.strftime('%Y%m%d_%H%M%S')}"
    admin_url = make_url(admin_database_url)
    if admin_url.get_backend_name() != "postgresql":
        raise RestoreVerificationError("Restore verification requires PostgreSQL admin credentials.")

    maintenance_url = admin_url.set(database="postgres")
    scratch_url = admin_url.set(database=scratch_name)
    maintenance_engine = create_engine(str(maintenance_url), isolation_level="AUTOCOMMIT", pool_pre_ping=True)
    scratch_engine = None

    try:
        with maintenance_engine.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{scratch_name}"'))

        restore_backup(str(scratch_url), backup)

        scratch_engine = create_engine(str(scratch_url), pool_pre_ping=True)
        with scratch_engine.connect() as connection:
            application_tables = int(
                connection.execute(
                    text(
                        """
                        SELECT count(*)
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_type = 'BASE TABLE'
                          AND table_name <> 'alembic_version'
                        """
                    )
                ).scalar_one()
            )
            if application_tables <= 0:
                raise RestoreVerificationError(
                    "Backup restored without any DairyOS application tables."
                )
            alembic_rows = int(
                connection.execute(
                    text(
                        """
                        SELECT count(*)
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_name = 'alembic_version'
                        """
                    )
                ).scalar_one()
            )

        completed = timestamp.isoformat().replace("+00:00", "Z")
        health["last_restore_verification"] = completed
        health["restore_verified"] = True
        health["restore_verified_backup"] = str(backup)
        health["restore_verified_application_tables"] = application_tables
        health["restore_verified_alembic_table_present"] = bool(alembic_rows)
        health.pop("restore_verification_error", None)
        _write_health(health_path, health)
        return {
            "verified_at": completed,
            "backup": str(backup),
            "application_tables": application_tables,
            "alembic_table_present": bool(alembic_rows),
        }
    except Exception as exc:
        health["restore_verified"] = False
        health["restore_verification_error"] = f"{type(exc).__name__}: {exc}"
        _write_health(health_path, health)
        if isinstance(exc, RestoreVerificationError):
            raise
        raise RestoreVerificationError(f"DairyOS scratch restore verification failed: {exc}") from exc
    finally:
        if scratch_engine is not None:
            scratch_engine.dispose()
        try:
            with maintenance_engine.connect() as connection:
                connection.execute(
                    text(
                        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                        "WHERE datname=:name AND pid <> pg_backend_pid()"
                    ),
                    {"name": scratch_name},
                )
                connection.execute(text(f'DROP DATABASE IF EXISTS "{scratch_name}"'))
        finally:
            maintenance_engine.dispose()
