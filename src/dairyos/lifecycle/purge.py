"""Destructive-data protection helpers for DairyOS uninstall."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from .manager import LifecycleError, LifecycleManager


PURGE_BACKUP_ROOT_NAME = "DairyOS-PurgeBackups"


def create_external_purge_backup(manager: LifecycleManager) -> Path:
    """Copy a complete lifecycle backup outside the data root before purge.

    A backup stored inside the directory being deleted is not a recovery
    artifact. The purge workflow therefore makes a second copy beside the data
    root so the backup survives deletion of the data root itself.
    """

    internal = manager.backup(label="pre-purge")
    parent = manager.data_root.parent / PURGE_BACKUP_ROOT_NAME
    parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = parent / f"{stamp}-pre-purge"
    shutil.copytree(internal, destination)
    return destination


def purge_data_after_backup(manager: LifecycleManager, create_backup: bool = True) -> Path | None:
    """Optionally create a surviving backup, then delete only the data root."""

    backup = create_external_purge_backup(manager) if create_backup else None
    if manager.data_root.exists():
        shutil.rmtree(manager.data_root, ignore_errors=False)
    return backup
