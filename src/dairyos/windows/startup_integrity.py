"""Startup integrity checks for the packaged DairyOS Windows runtime.

The packaged appliance must distinguish a genuinely new farm from an
established installation whose database has unexpectedly disappeared. The
latter condition is safety-critical: DairyOS must block startup rather than
silently creating an empty farm.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

from dairyos.platform import paths


MARKER_FILENAME = "DairyOS-installation-state.json"
MARKER_ENV_VAR = "DAIRYOS_INSTALLATION_STATE"
MARKER_VERSION = 1


class StartupIntegrityError(RuntimeError):
    """Raised when startup could silently discard an established farm."""


@dataclass(frozen=True)
class StartupIntegrityFacts:
    data_root: Path
    marker_path: Path
    prior_installation: bool
    persistent_data: bool
    application_tables: int

    @property
    def recovery_required(self) -> bool:
        return self.application_tables == 0 and (
            self.prior_installation or self.persistent_data
        )


def _is_packaged_windows() -> bool:
    return os.name == "nt" and bool(getattr(sys, "frozen", False))


def marker_path() -> Path:
    """Return the durable installation marker path outside farm data."""
    override = os.environ.get(MARKER_ENV_VAR)
    if override:
        return Path(override).expanduser()

    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / MARKER_FILENAME

    return Path.home() / MARKER_FILENAME


def prior_installation_exists() -> bool:
    return marker_path().is_file()


def record_successful_start(*, data_root: Path | None = None) -> Path | None:
    """Record that the packaged appliance reached a healthy application start."""
    if not _is_packaged_windows():
        return None

    target = marker_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    root = data_root or paths.data_root(create=False)
    payload = {
        "version": MARKER_VERSION,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "data_root": str(root),
    }
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)
    return target


def inspect_startup_integrity(
    *,
    application_tables: int,
    enforce: bool | None = None,
) -> StartupIntegrityFacts:
    """Return startup facts and block unsafe empty-database bootstrap."""
    root = paths.data_root(create=False)
    marker = marker_path()

    persistent_data = False
    if root.exists():
        ignored = {
            "backups",
            "logs",
            "postgres",
            "installation_state.json",
            "lifecycle.json",
        }
        persistent_data = any(item.name not in ignored for item in root.iterdir())

    facts = StartupIntegrityFacts(
        data_root=root,
        marker_path=marker,
        prior_installation=marker.is_file(),
        persistent_data=persistent_data,
        application_tables=application_tables,
    )

    if enforce is None:
        enforce = _is_packaged_windows()

    if enforce and facts.recovery_required:
        backup_hint = (
            f" Verified backups are available under: {root / 'backups'}."
            if (root / "backups").is_dir()
            else " No local backup directory was detected."
        )
        raise StartupIntegrityError(
            "DairyOS startup is blocked: an established installation was detected "
            "but the application database is empty or unavailable. "
            "DairyOS will not create a new empty farm or hide the existing farm. "
            "Data recovery is required before normal startup."
            + backup_hint
        )

    return facts
