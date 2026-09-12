"""Durable, explicit installation/recovery choices for the Windows installer.

The Inno Setup wizard cannot safely perform PostgreSQL recovery itself.  It
therefore records one small, atomically-written request for the packaged
supervisor.  The supervisor applies the request only after the private
database has been prepared and before the normal backend starts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile


PENDING_INSTALLATION_CHOICE_FILENAME = "pending-installation-choice.json"
INSTALLATION_CHOICE_VERSION = 1
VALID_INSTALLATION_CHOICES = frozenset({"clean", "restore", "keep"})


class InstallationChoiceError(RuntimeError):
    """Raised when an installer recovery request is invalid."""


@dataclass(frozen=True)
class InstallationChoice:
    mode: str
    backup_path: Path | None
    requested_at: str


def pending_installation_choice_path(data_root: str | Path) -> Path:
    return Path(data_root).expanduser().resolve() / PENDING_INSTALLATION_CHOICE_FILENAME


def write_pending_installation_choice(
    data_root: str | Path,
    *,
    mode: str,
    backup_path: str | Path | None = None,
) -> Path:
    normalized_mode = str(mode or "").strip().lower()
    if normalized_mode not in VALID_INSTALLATION_CHOICES:
        raise InstallationChoiceError(
            "Installation choice must be either 'clean' or 'restore'."
        )

    normalized_backup: str | None = None
    if normalized_mode == "restore":
        if backup_path is None or not str(backup_path).strip():
            raise InstallationChoiceError(
                "Restore installation choice requires an explicit backup path."
            )
        normalized_backup = str(Path(backup_path).expanduser().resolve())
    elif backup_path is not None:
        raise InstallationChoiceError(
            "Installation choice cannot include a backup path unless restore is selected."
        )

    target = pending_installation_choice_path(data_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": INSTALLATION_CHOICE_VERSION,
        "mode": normalized_mode,
        "backup_path": normalized_backup,
        "requested_at": datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
    }
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=target.parent,
    )
    try:
        with os.fdopen(
            file_descriptor,
            "w",
            encoding="utf-8",
            newline="\n",
        ) as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, target)
    finally:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
    return target


def read_pending_installation_choice(
    data_root: str | Path,
) -> InstallationChoice | None:
    path = pending_installation_choice_path(data_root)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallationChoiceError(
            f"DairyOS installation choice cannot be read: {path}"
        ) from exc
    if not isinstance(payload, dict):
        raise InstallationChoiceError("DairyOS installation choice is not an object.")
    if payload.get("version") != INSTALLATION_CHOICE_VERSION:
        raise InstallationChoiceError(
            "DairyOS installation choice has an unsupported version."
        )

    mode = str(payload.get("mode") or "").strip().lower()
    if mode not in VALID_INSTALLATION_CHOICES:
        raise InstallationChoiceError(
            "DairyOS installation choice contains an unsupported mode."
        )
    raw_backup = payload.get("backup_path")
    if mode == "restore":
        if not isinstance(raw_backup, str) or not raw_backup.strip():
            raise InstallationChoiceError(
                "DairyOS restore choice does not contain an explicit backup path."
            )
        backup = Path(raw_backup).expanduser().resolve()
    else:
        if raw_backup not in (None, ""):
            raise InstallationChoiceError(
                "DairyOS non-restore choice unexpectedly contains a backup path."
            )
        backup = None

    requested_at = str(payload.get("requested_at") or "").strip()
    if not requested_at:
        raise InstallationChoiceError(
            "DairyOS installation choice does not contain a request timestamp."
        )

    return InstallationChoice(mode, backup, requested_at)


def clear_pending_installation_choice(data_root: str | Path) -> None:
    pending_installation_choice_path(data_root).unlink(missing_ok=True)
