"""DairyOS first-run and reinstall state management."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from typing import Final

from dairyos.platform import paths


STATE_FILENAME: Final[str] = "installation_state.json"


class InstallationStateError(RuntimeError):
    """Raised when DairyOS installation state is invalid."""


class FarmLaunchMode(str, Enum):
    """Explicit operator choice when existing DairyOS data is present."""

    EXISTING = "existing"
    NEW = "new"
    RESTORE = "restore"


@dataclass(frozen=True)
class InstallationState:
    installation_id: str
    created_at: str
    last_started_at: str | None = None
    farm_initialized: bool = False
    database_initialized: bool = False
    database_name: str = "dairyos"
    database_owner: str = "dairyos"

    def as_dict(self) -> dict[str, object]:
        return {
            "installation_id": self.installation_id,
            "created_at": self.created_at,
            "last_started_at": self.last_started_at,
            "farm_initialized": self.farm_initialized,
            "database_initialized": self.database_initialized,
            "database_name": self.database_name,
            "database_owner": self.database_owner,
        }


@dataclass(frozen=True)
class InstallationFacts:
    data_root: Path
    state_file: Path
    state_exists: bool
    lifecycle_manifest_exists: bool
    backup_count: int
    persistent_files_exist: bool

    @property
    def is_new_installation(self) -> bool:
        return not (
            self.state_exists
            or self.lifecycle_manifest_exists
            or self.persistent_files_exist
        )

    @property
    def has_existing_data(self) -> bool:
        return not self.is_new_installation


def state_path() -> Path:
    return paths.data_root(create=False) / STATE_FILENAME


def inspect_installation() -> InstallationFacts:
    root = paths.data_root(create=False)
    state = root / STATE_FILENAME
    lifecycle_manifest = root / "lifecycle.json"
    backups = root / "backups"

    persistent_files_exist = False
    if root.exists():
        for item in root.iterdir():
            if item.name in {STATE_FILENAME, "lifecycle.json", "backups", "logs"}:
                continue
            persistent_files_exist = True
            break

    backup_count = 0
    if backups.is_dir():
        backup_count = sum(1 for item in backups.iterdir() if item.is_dir())

    return InstallationFacts(
        data_root=root,
        state_file=state,
        state_exists=state.is_file(),
        lifecycle_manifest_exists=lifecycle_manifest.is_file(),
        backup_count=backup_count,
        persistent_files_exist=persistent_files_exist,
    )


def load_state() -> InstallationState | None:
    path = state_path()

    if not path.is_file():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallationStateError(
            f"DairyOS installation state cannot be read: {path}"
        ) from exc

    required = {"installation_id", "created_at"}
    missing = sorted(required - payload.keys())
    if missing:
        raise InstallationStateError(
            "DairyOS installation state is incomplete; missing: "
            + ", ".join(missing)
        )

    return InstallationState(
        installation_id=str(payload["installation_id"]),
        created_at=str(payload["created_at"]),
        last_started_at=(
            str(payload["last_started_at"])
            if payload.get("last_started_at") is not None
            else None
        ),
        farm_initialized=bool(payload.get("farm_initialized", False)),
        database_initialized=bool(payload.get("database_initialized", False)),
        database_name=str(payload.get("database_name", "dairyos")),
        database_owner=str(payload.get("database_owner", "dairyos")),
    )


def write_state(state: InstallationState) -> Path:
    root = paths.data_root(create=True)
    target = root / STATE_FILENAME
    temporary = target.with_suffix(target.suffix + ".tmp")

    try:
        temporary.write_text(
            json.dumps(state.as_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(target)
    except OSError as exc:
        raise InstallationStateError(
            f"DairyOS installation state could not be written: {target}"
        ) from exc

    return target


def require_explicit_mode(
    facts: InstallationFacts,
    mode: FarmLaunchMode | None,
) -> FarmLaunchMode:
    if facts.is_new_installation:
        return FarmLaunchMode.NEW

    if mode is None:
        raise InstallationStateError(
            "Existing DairyOS farm data was detected. An explicit launch mode "
            "is required: existing, new, or restore."
        )

    return mode


def validate_new_installation(facts: InstallationFacts) -> None:
    if facts.has_existing_data:
        raise InstallationStateError(
            "A new DairyOS farm cannot be created automatically because "
            "existing DairyOS data is present."
        )


def validate_existing_installation(
    facts: InstallationFacts,
    mode: FarmLaunchMode,
) -> None:
    resolved = require_explicit_mode(facts, mode)

    if resolved is FarmLaunchMode.RESTORE and facts.backup_count == 0:
        raise InstallationStateError(
            "Restore was selected, but no DairyOS backups are available."
        )


def choose_existing_backup(facts: InstallationFacts) -> Path:
    if facts.backup_count == 0:
        raise InstallationStateError(
            "No DairyOS backup is available for restoration."
        )

    backups = facts.data_root / "backups"
    candidates = sorted(
        (item for item in backups.iterdir() if item.is_dir()),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )

    if not candidates:
        raise InstallationStateError(
            "DairyOS backup count was non-zero but no backup directory was found."
        )

    return candidates[0]