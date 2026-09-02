"""Automatic, redundant PostgreSQL protection for DairyOS farm data.

The normal backup cadence is every six hours (scheduled by the Windows backup
worker).  Each run creates and verifies a primary custom-format PostgreSQL dump,
then creates an independently checksum-verified mirror copy.  The first
successful run in each calendar month also creates a separately named monthly
archive that is outside the rolling backup set.

When a second physical drive is available on Windows it is selected
automatically.  If only the live-data drive is available, DairyOS still creates
an independent local mirror but records the state as degraded rather than
pretending that it protects against disk loss.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import ctypes
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Iterable

from dairyos.data.database.backup import (
    PostgreSQLBackupError,
    create_backup,
    verify_backup_archive,
    verify_backup_checksum,
)
from dairyos.platform import paths


ROLLING_KEEP = 120  # 4 per day x 30 days
MONTHLY_KEEP = 60   # five years of monthly recovery points
BACKUP_HEALTH_FILENAME = "backup-health.json"


@dataclass(frozen=True)
class BackupDestination:
    root: Path
    physically_redundant: bool
    degraded_reason: str | None = None


@dataclass(frozen=True)
class AutomaticBackupResult:
    primary: Path
    mirror: Path
    monthly_primary: Path | None
    monthly_mirror: Path | None
    sha256: str
    physically_redundant: bool
    health_path: Path


def _utc_now(now: datetime | None = None) -> datetime:
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _safe_json_write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
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


def _is_writable_directory(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".dairyos-backup-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def _same_storage_device(first: Path, second: Path) -> bool:
    """Best-effort determination of whether two paths share the same volume."""
    first_resolved = first.resolve()
    second_resolved = second.resolve()

    if os.name == "nt":
        return first_resolved.drive.lower() == second_resolved.drive.lower()

    try:
        return os.stat(first_resolved).st_dev == os.stat(second_resolved).st_dev
    except OSError:
        return True


def _windows_candidate_drives(primary_root: Path) -> Iterable[Path]:
    if os.name != "nt":
        return ()

    DRIVE_REMOVABLE = 2
    DRIVE_FIXED = 3
    kernel32 = ctypes.windll.kernel32
    primary_drive = primary_root.resolve().drive.lower()
    fixed: list[Path] = []
    removable: list[Path] = []

    for ordinal in range(ord("C"), ord("Z") + 1):
        root = Path(f"{chr(ordinal)}:\\")
        if root.drive.lower() == primary_drive or not root.exists():
            continue
        drive_type = int(kernel32.GetDriveTypeW(str(root)))
        if drive_type == DRIVE_FIXED:
            fixed.append(root)
        elif drive_type == DRIVE_REMOVABLE:
            removable.append(root)

    return (*fixed, *removable)


def choose_mirror_destination(data_root: Path | None = None) -> BackupDestination:
    root = (data_root or paths.data_root(create=True)).resolve()
    override = os.environ.get("DAIRYOS_BACKUP_MIRROR_ROOT", "").strip()

    if override:
        candidate = Path(override).expanduser().resolve()
        if _is_writable_directory(candidate):
            redundant = not _same_storage_device(root, candidate)
            return BackupDestination(
                candidate,
                physically_redundant=redundant,
                degraded_reason=(
                    None
                    if redundant
                    else "Configured mirror is on the same storage device as live DairyOS data."
                ),
            )

    for drive in _windows_candidate_drives(root):
        candidate = drive / "DairyOS-Backups"
        if _is_writable_directory(candidate):
            return BackupDestination(candidate, physically_redundant=True)

    fallback = root / "backups" / "mirror"
    fallback.mkdir(parents=True, exist_ok=True)
    return BackupDestination(
        fallback,
        physically_redundant=False,
        degraded_reason=(
            "No writable second physical drive was available. DairyOS created a second "
            "local copy, but a failure of the live-data disk could still affect both copies."
        ),
    )


def _copy_and_verify(source: Path, destination: Path, sha256: str) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    shutil.copy2(source, temporary)
    verify_backup_checksum(temporary, sha256)
    os.replace(temporary, destination)
    verify_backup_checksum(destination, sha256)
    return destination


def _metadata_path(dump_path: Path) -> Path:
    return dump_path.with_suffix(dump_path.suffix + ".json")


def _write_backup_metadata(
    dump_path: Path,
    *,
    created_at: datetime,
    sha256: str,
    size_bytes: int,
    kind: str,
    source: str,
) -> None:
    _safe_json_write(
        _metadata_path(dump_path),
        {
            "version": 1,
            "kind": kind,
            "created_at": created_at.isoformat().replace("+00:00", "Z"),
            "file": dump_path.name,
            "size_bytes": size_bytes,
            "sha256": sha256,
            "archive_verified": True,
            "source": source,
        },
    )


def _prune(directory: Path, prefix: str, keep: int) -> None:
    dumps = sorted(
        directory.glob(f"{prefix}*.dump"),
        key=lambda item: item.name,
        reverse=True,
    )
    for stale in dumps[keep:]:
        stale.unlink(missing_ok=True)
        _metadata_path(stale).unlink(missing_ok=True)


def backup_health_path(data_root: Path | None = None) -> Path:
    root = (data_root or paths.data_root(create=True)).resolve()
    return root / "backups" / BACKUP_HEALTH_FILENAME


def read_backup_health(data_root: Path | None = None) -> dict[str, object]:
    path = backup_health_path(data_root)
    if not path.is_file():
        return {
            "status": "NEVER_RUN",
            "last_successful_backup": None,
            "physically_redundant": False,
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "status": "INVALID_HEALTH_RECORD",
            "last_successful_backup": None,
            "physically_redundant": False,
        }
    return payload if isinstance(payload, dict) else {"status": "INVALID_HEALTH_RECORD"}


def run_automatic_backup(
    database_url: str,
    *,
    data_root: Path | None = None,
    mirror_destination: BackupDestination | None = None,
    now: datetime | None = None,
) -> AutomaticBackupResult:
    """Create, verify, mirror, archive, and record one scheduled backup run."""

    root = (data_root or paths.data_root(create=True)).resolve()
    timestamp = _utc_now(now)
    stamp = timestamp.strftime("%Y%m%dT%H%M%SZ")
    month = timestamp.strftime("%Y-%m")
    backup_root = root / "backups"
    primary_root = backup_root / "automatic" / "primary"
    monthly_root = backup_root / "monthly"
    destination = mirror_destination or choose_mirror_destination(root)
    mirror_root = destination.root / "automatic"
    mirror_monthly_root = destination.root / "monthly"
    health = backup_health_path(root)

    primary_root.mkdir(parents=True, exist_ok=True)
    monthly_root.mkdir(parents=True, exist_ok=True)
    mirror_root.mkdir(parents=True, exist_ok=True)
    mirror_monthly_root.mkdir(parents=True, exist_ok=True)

    previous_health = read_backup_health(root)

    try:
        primary = primary_root / f"DairyOS-Auto-{stamp}.dump"
        create_backup(database_url, primary)
        metadata = verify_backup_archive(primary)
        sha256 = str(metadata["sha256"])
        size_bytes = int(metadata["size_bytes"])
        _write_backup_metadata(
            primary,
            created_at=timestamp,
            sha256=sha256,
            size_bytes=size_bytes,
            kind="ROLLING_PRIMARY",
            source="live-database",
        )

        mirror = mirror_root / primary.name
        _copy_and_verify(primary, mirror, sha256)
        _write_backup_metadata(
            mirror,
            created_at=timestamp,
            sha256=sha256,
            size_bytes=size_bytes,
            kind="ROLLING_MIRROR",
            source=str(primary),
        )

        monthly_primary: Path | None = None
        monthly_mirror: Path | None = None
        existing_monthly = list(monthly_root.glob(f"DairyOS-Monthly-{month}-*.dump"))
        if not existing_monthly:
            monthly_name = f"DairyOS-Monthly-{month}-{stamp}.dump"
            monthly_primary = monthly_root / monthly_name
            _copy_and_verify(primary, monthly_primary, sha256)
            _write_backup_metadata(
                monthly_primary,
                created_at=timestamp,
                sha256=sha256,
                size_bytes=size_bytes,
                kind="MONTHLY_ARCHIVE_PRIMARY",
                source=str(primary),
            )

            monthly_mirror = mirror_monthly_root / monthly_name
            _copy_and_verify(primary, monthly_mirror, sha256)
            _write_backup_metadata(
                monthly_mirror,
                created_at=timestamp,
                sha256=sha256,
                size_bytes=size_bytes,
                kind="MONTHLY_ARCHIVE_MIRROR",
                source=str(primary),
            )

        _prune(primary_root, "DairyOS-Auto-", ROLLING_KEEP)
        _prune(mirror_root, "DairyOS-Auto-", ROLLING_KEEP)
        _prune(monthly_root, "DairyOS-Monthly-", MONTHLY_KEEP)
        _prune(mirror_monthly_root, "DairyOS-Monthly-", MONTHLY_KEEP)

        success = timestamp.isoformat().replace("+00:00", "Z")
        _safe_json_write(
            health,
            {
                "version": 1,
                "status": "HEALTHY" if destination.physically_redundant else "DEGRADED",
                "last_attempt": success,
                "last_successful_backup": success,
                "primary": str(primary),
                "mirror": str(mirror),
                "monthly_primary": str(monthly_primary) if monthly_primary else None,
                "monthly_mirror": str(monthly_mirror) if monthly_mirror else None,
                "sha256": sha256,
                "archive_verified": True,
                "physically_redundant": destination.physically_redundant,
                "degraded_reason": destination.degraded_reason,
                "rolling_retention": ROLLING_KEEP,
                "monthly_retention": MONTHLY_KEEP,
            },
        )

        return AutomaticBackupResult(
            primary=primary,
            mirror=mirror,
            monthly_primary=monthly_primary,
            monthly_mirror=monthly_mirror,
            sha256=sha256,
            physically_redundant=destination.physically_redundant,
            health_path=health,
        )
    except Exception as exc:
        failed_at = timestamp.isoformat().replace("+00:00", "Z")
        _safe_json_write(
            health,
            {
                "version": 1,
                "status": "FAILED",
                "last_attempt": failed_at,
                "last_successful_backup": previous_health.get("last_successful_backup"),
                "physically_redundant": previous_health.get("physically_redundant", False),
                "error": f"{type(exc).__name__}: {exc}",
            },
        )
        if isinstance(exc, PostgreSQLBackupError):
            raise
        raise PostgreSQLBackupError(f"Automatic DairyOS backup failed: {exc}") from exc
