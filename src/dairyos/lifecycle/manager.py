"""Transactional lifecycle primitives for DairyOS deployments.

The lifecycle boundary deliberately separates runtime installation files from
farm data. Farm data lives under ``dairyos.platform.paths.data_root()`` and is
never deleted by a normal uninstall. Destructive deletion requires an explicit
purge mode and a confirmation token.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable

from dairyos.data.database.backup import PostgreSQLBackupError, create_backup, restore_backup
from dairyos.platform import paths


MANIFEST_NAME = "lifecycle.json"
PURGE_CONFIRMATION = "PURGE DAIRYOS DATA"
MIN_PYTHON = (3, 12)


class LifecycleError(RuntimeError):
    """Base error for lifecycle operations."""


class LifecycleValidationError(LifecycleError):
    """Raised when the installation fails a lifecycle validation gate."""


class UninstallMode(str, Enum):
    KEEP_DATA = "keep-data"
    PURGE_DATA = "purge-data"


@dataclass(frozen=True)
class LifecycleManifest:
    installed_at: str
    updated_at: str
    application_version: str
    python_version: str
    data_root: str
    installation_root: str
    last_backup: str | None = None
    source_revision: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "installed_at": self.installed_at,
            "updated_at": self.updated_at,
            "application_version": self.application_version,
            "python_version": self.python_version,
            "data_root": self.data_root,
            "installation_root": self.installation_root,
            "last_backup": self.last_backup,
            "source_revision": self.source_revision,
        }


class LifecycleManager:
    """Coordinate installation, validation, backup, restore and uninstall.

    Package installation itself is intentionally delegated to the caller. The
    manager provides the durable transaction boundary around that operation:
    create data roots, snapshot data before mutation, validate the resulting
    runtime, restore the snapshot on failure, and remove runtime files without
    implicitly removing farm data.
    """

    def __init__(
        self,
        installation_root: str | Path,
        data_root: str | Path | None = None,
        database_url: str | None = None,
    ) -> None:
        self.installation_root = Path(installation_root).expanduser().resolve()
        self.data_root = Path(data_root).expanduser().resolve() if data_root else paths.data_root(create=False).resolve()
        self.database_url = database_url or os.environ.get("DAIRYOS_DATABASE_URL")

    @property
    def manifest_path(self) -> Path:
        return self.data_root / MANIFEST_NAME

    @property
    def backup_root(self) -> Path:
        return self.data_root / "backups"

    def install(self, application_version: str | None = None, source_revision: str | None = None) -> LifecycleManifest:
        self._ensure_data_layout()
        now = _utc_now()
        previous = self._read_manifest()
        manifest = LifecycleManifest(
            installed_at=previous.get("installed_at", now) if previous else now,
            updated_at=now,
            application_version=application_version or _package_version(),
            python_version=_python_version(),
            data_root=str(self.data_root),
            installation_root=str(self.installation_root),
            last_backup=previous.get("last_backup") if previous else None,
            source_revision=source_revision,
        )
        _write_json_atomic(self.manifest_path, manifest.as_dict())
        return manifest

    def validate(self, require_database: bool = True) -> dict[str, object]:
        errors: list[str] = []
        if sys.version_info[:2] < MIN_PYTHON:
            errors.append(
                f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer is required; "
                f"found {_python_version()}"
            )

        if not self.data_root.exists():
            errors.append(f"Data root does not exist: {self.data_root}")
        else:
            for directory in (self.data_root / "storage", self.data_root / "backups", self.data_root / "logs"):
                if not directory.exists():
                    errors.append(f"Required data directory is missing: {directory}")
                elif not _is_writable(directory):
                    errors.append(f"Required data directory is not writable: {directory}")

        if not self.installation_root.exists():
            errors.append(f"Installation root does not exist: {self.installation_root}")

        manifest = self._read_manifest()
        if not manifest:
            errors.append(f"Lifecycle manifest is missing: {self.manifest_path}")

        database_checked = False
        if require_database:
            if not self.database_url:
                errors.append("DAIRYOS_DATABASE_URL is not configured")
            else:
                database_checked = True
                try:
                    _check_database(self.database_url)
                except Exception as exc:  # pragma: no cover - environment-specific
                    errors.append(f"Database validation failed: {exc}")

        result = {
            "valid": not errors,
            "errors": errors,
            "python": _python_version(),
            "data_root": str(self.data_root),
            "installation_root": str(self.installation_root),
            "database_checked": database_checked,
            "manifest": manifest,
        }
        if errors:
            raise LifecycleValidationError(json.dumps(result, indent=2))
        return result

    def backup(self, label: str = "pre-change") -> Path:
        self._ensure_data_layout()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        destination = self.backup_root / f"{timestamp}-{_safe_label(label)}"
        staging_parent = self.backup_root / ".staging"
        staging_parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix="backup-", dir=staging_parent))
        try:
            files_root = staging / "files"
            files_root.mkdir(parents=True, exist_ok=True)
            manifest_entries: list[dict[str, object]] = []
            for source in self.data_root.rglob("*"):
                if not source.is_file():
                    continue
                relative = source.relative_to(self.data_root)
                if relative.parts and relative.parts[0] == "backups":
                    continue
                target = files_root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                manifest_entries.append(
                    {
                        "path": relative.as_posix(),
                        "size_bytes": target.stat().st_size,
                        "sha256": _sha256(target),
                    }
                )

            database_backup: str | None = None
            if self.database_url:
                try:
                    db_path = staging / "database.dump"
                    create_backup(self.database_url, db_path)
                    database_backup = db_path.name
                except PostgreSQLBackupError as exc:
                    raise LifecycleError(f"Database backup failed: {exc}") from exc

            backup_manifest = {
                "created_at": _utc_now(),
                "label": label,
                "application_version": _package_version(),
                "python_version": _python_version(),
                "data_root": str(self.data_root),
                "installation_root": str(self.installation_root),
                "files": manifest_entries,
                "database_backup": database_backup,
            }
            _write_json_atomic(staging / "backup.json", backup_manifest)
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staging, destination)
            staging = None  # type: ignore[assignment]

            current = self._read_manifest()
            if current:
                current["last_backup"] = str(destination)
                current["updated_at"] = _utc_now()
                _write_json_atomic(self.manifest_path, current)
            return destination
        finally:
            if staging is not None and staging.exists():
                shutil.rmtree(staging, ignore_errors=True)

    def restore(self, backup: str | Path) -> None:
        backup_path = Path(backup).expanduser().resolve()
        backup_manifest_path = backup_path / "backup.json"
        if not backup_manifest_path.is_file():
            raise LifecycleError(f"Invalid DairyOS backup: {backup_path}")
        backup_manifest = json.loads(backup_manifest_path.read_text(encoding="utf-8"))

        files_root = backup_path / "files"
        if files_root.exists():
            self._ensure_data_layout()
            for source in files_root.rglob("*"):
                if not source.is_file():
                    continue
                relative = source.relative_to(files_root)
                destination = self.data_root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)

        database_backup = backup_manifest.get("database_backup")
        if database_backup:
            if not self.database_url:
                raise LifecycleError("Backup contains a database dump but no database URL is configured")
            restore_backup(self.database_url, backup_path / str(database_backup))

    def rollback(self, backup: str | Path) -> dict[str, object]:
        self.restore(backup)
        return self.validate(require_database=bool(self.database_url))

    def upgrade(
        self,
        upgrade_action: Callable[[], None],
        validate_after: Callable[[], None] | None = None,
        source_revision: str | None = None,
    ) -> Path:
        """Backup first, run the caller's upgrade, then validate or rollback.

        The caller owns package/environment replacement. This method supplies
        the durable data transaction and guarantees that a failed validation
        restores the pre-upgrade data snapshot before the exception escapes.
        """

        backup_path = self.backup(label="pre-upgrade")
        try:
            upgrade_action()
            if validate_after is not None:
                validate_after()
            else:
                self.validate(require_database=bool(self.database_url))
            self.install(source_revision=source_revision)
            return backup_path
        except Exception:
            self.rollback(backup_path)
            raise

    def uninstall(self, mode: UninstallMode, confirmation: str | None = None, backup_before_purge: bool = True) -> None:
        if mode is UninstallMode.PURGE_DATA:
            if confirmation != PURGE_CONFIRMATION:
                raise LifecycleError(
                    f"Permanent purge requires the exact confirmation token: {PURGE_CONFIRMATION!r}"
                )
            if backup_before_purge:
                self.backup(label="pre-purge")
            shutil.rmtree(self.data_root, ignore_errors=False)

        if self.installation_root.exists():
            shutil.rmtree(self.installation_root, ignore_errors=False)

    def _ensure_data_layout(self) -> None:
        self.data_root.mkdir(parents=True, exist_ok=True)
        for name in ("storage", "backups", "logs"):
            (self.data_root / name).mkdir(parents=True, exist_ok=True)

    def _read_manifest(self) -> dict[str, object] | None:
        if not self.manifest_path.is_file():
            return None
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _python_version() -> str:
    return ".".join(str(part) for part in sys.version_info[:3])


def _package_version() -> str:
    try:
        return importlib.metadata.version("dairyos")
    except importlib.metadata.PackageNotFoundError:
        return "source"


def _safe_label(label: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in label).strip("-") or "backup"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_writable(directory: Path) -> bool:
    try:
        probe = directory / ".dairyo_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def _check_database(database_url: str) -> None:
    """Validate a DairyOS SQLAlchemy database URL using psycopg.

    DairyOS exposes PostgreSQL URLs in SQLAlchemy form, for example
    ``postgresql+psycopg://user:password@host:5432/database``.  psycopg's
    direct ``connect()`` call expects libpq-style connection information or
    a plain PostgreSQL URI and therefore does not accept the SQLAlchemy
    ``+psycopg`` driver suffix.  Parse the canonical URL with SQLAlchemy and
    pass the resulting connection fields to psycopg explicitly.
    """
    import psycopg
    from sqlalchemy.engine import make_url

    parsed = make_url(database_url)
    connect_args = parsed.translate_connect_args(
        host="host",
        port="port",
        username="user",
        password="password",
        database="dbname",
    )

    # Preserve SQLAlchemy URL query options where they map directly to
    # libpq/psycopg keyword arguments, such as sslmode or application_name.
    connect_args.update(parsed.query)

    with psycopg.connect(connect_timeout=5, **connect_args) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()


def _write_json_atomic(path: Path, payload: object) -> None:
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
