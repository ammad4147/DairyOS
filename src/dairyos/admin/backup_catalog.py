"""Read-only discovery and current integrity checks for restore candidates."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from dairyos.data.database.backup import (
    PostgreSQLBackupError,
    verify_backup_archive,
    verify_backup_checksum,
)
from dairyos.lifecycle.backup_validation import contained_file, verified_manifest
from dairyos.lifecycle.manager import LifecycleError


@dataclass(frozen=True)
class VerifiedBackup:
    path: Path
    kind: str
    created_at: str
    label: str
    size_bytes: int

    @property
    def display_name(self) -> str:
        scope = "Full farm snapshot" if self.kind == "snapshot" else "Database only"
        return f"{self.created_at} | {scope} | {self.label} | {self.path}"


def _contained(root: Path, relative: object) -> Path:
    return contained_file(root, relative)


def _read_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise LifecycleError("Backup metadata must be a JSON object.")
    return value


def verify_restore_candidate(backup: str | Path) -> VerifiedBackup:
    """Recheck checksums and the archive catalog; never mutate the farm."""
    path = Path(backup).expanduser().resolve()
    if any(part.startswith(".staging") for part in path.parts):
        raise LifecycleError("Incomplete staging backups cannot be restored.")
    if path.is_dir():
        manifest = verified_manifest(path)
        if manifest.get("database_backup_archive_verified") is not True:
            raise LifecycleError("Snapshot has no verified PostgreSQL archive.")
        dump = _contained(path, manifest.get("database_backup"))
        expected_dump = manifest.get("database_backup_sha256")
        if not expected_dump:
            raise LifecycleError("Snapshot is missing its PostgreSQL SHA-256 checksum.")
        verify_backup_checksum(dump, str(expected_dump))
        kind = "snapshot"
    elif path.suffix.lower() == ".dump":
        manifest = _read_object(path.with_suffix(path.suffix + ".json"))
        if manifest.get("archive_verified") is not True:
            raise LifecycleError("Database backup has not been archive-verified.")
        if manifest.get("file") != path.name:
            raise LifecycleError("Database backup metadata names a different file.")
        verify_backup_checksum(path, str(manifest.get("sha256") or ""))
        dump = path
        kind = "database"
    else:
        raise LifecycleError(
            "Choose a full snapshot directory or a verified .dump file."
        )
    metadata = verify_backup_archive(dump)
    recorded_size = manifest.get(
        "size_bytes" if kind == "database" else "database_backup_size_bytes"
    )
    if recorded_size is not None and int(recorded_size) != metadata["size_bytes"]:
        raise LifecycleError("Database backup size does not match its metadata.")
    created = str(manifest.get("created_at") or "")
    if not created:
        created = datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat()
    # Validate dates so corrupt metadata cannot reorder the recovery choices.
    created = datetime.fromisoformat(created).astimezone(UTC).isoformat()
    return VerifiedBackup(
        path,
        kind,
        created,
        str(manifest.get("label") or manifest.get("kind") or path.name),
        int(metadata["size_bytes"]),
    )


def backup_search_roots(data_root: Path) -> list[Path]:
    """Known DairyOS locations, not an unbounded search of the user's disks."""
    root = data_root.expanduser().resolve()
    roots = [
        root / "backups",
        root.parent / "recovery",
        root.parent / "DairyOS-PurgeBackups",
    ]
    for key in ("DAIRYOS_BACKUP_MIRROR_ROOT", "DAIRYOS_RECOVERY_ROOT"):
        if os.environ.get(key):
            roots.append(Path(os.environ[key]).expanduser())
    roots.extend(
        Path(value).expanduser()
        for value in os.environ.get("DAIRYOS_BACKUP_SEARCH_ROOTS", "").split(os.pathsep)
        if value
    )
    if os.name == "nt":
        roots.extend(
            Path(f"{chr(letter)}:/DairyOS-Backups")
            for letter in range(ord("C"), ord("Z") + 1)
        )
    # The health record retains a configured mirror destination after a restart.
    try:
        health = _read_object(root / "backups" / "backup-health.json")
        for key in ("primary", "mirror", "monthly_primary", "monthly_mirror"):
            value = health.get(key)
            if value and Path(str(value)).is_absolute():
                roots.append(Path(str(value)).parent)
    except (OSError, ValueError, LifecycleError):
        pass
    return list(dict.fromkeys(path.resolve() for path in roots))


def discover_verified_backups(
    data_root: Path, *, roots: list[Path] | None = None
) -> tuple[list[VerifiedBackup], list[str]]:
    candidates: set[Path] = set()
    problems: list[str] = []
    seen: set[Path] = set()

    def visit(path: Path, depth: int) -> None:
        if path.is_symlink() or path.name.startswith("."):
            return
        resolved = path.resolve()
        if resolved in seen:
            return
        seen.add(resolved)
        try:
            if path.is_file():
                if path.suffix.lower() == ".dump":
                    candidates.add(resolved)
                return
            if not path.exists():
                return
            if (path / "backup.json").is_file():
                candidates.add(resolved)
                return
            if depth < 4:
                for child in path.iterdir():
                    visit(child, depth + 1)
        except OSError as exc:
            problems.append(f"Cannot inspect {path}: {type(exc).__name__}")

    for root in roots if roots is not None else backup_search_roots(data_root):
        visit(Path(root), 0)
    verified: list[VerifiedBackup] = []
    for path in sorted(candidates):
        try:
            verified.append(verify_restore_candidate(path))
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            LifecycleError,
            PostgreSQLBackupError,
        ) as exc:
            problems.append(f"Not offered: {path}: {type(exc).__name__}")
    verified.sort(key=lambda item: (item.created_at, str(item.path)), reverse=True)
    return verified, problems
