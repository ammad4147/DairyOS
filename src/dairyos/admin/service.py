"""Application service for privileged DairyOS lifecycle administration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dairyos.lifecycle.manager import LifecycleError, LifecycleManager, UninstallMode
from dairyos.lifecycle.purge import create_external_purge_backup, purge_data_after_backup
from dairyos.lifecycle.restore import restore_snapshot

RESET_CONFIRMATION = "RESET DAIRYOS DATA"


@dataclass(frozen=True)
class AdminResult:
    operation: str
    success: bool
    message: str
    artifact: str | None = None


class AdminService:
    """Thin administrative facade over the canonical lifecycle boundary.

    This service deliberately contains no farm-domain business logic. It is
    the integration point used by the separate administrative application.
    """

    def __init__(self, manager: LifecycleManager):
        self.manager = manager

    def status(self) -> dict[str, object]:
        return self.manager.validate(require_database=bool(self.manager.database_url))

    def backup(self, label: str = "admin") -> AdminResult:
        artifact = self.manager.backup(label=label)
        return AdminResult("backup", True, "Backup completed.", str(artifact))

    def restore(self, backup: str | Path) -> AdminResult:
        restore_snapshot(self.manager, backup)
        self.manager.validate(require_database=bool(self.manager.database_url))
        return AdminResult("restore", True, "Snapshot restored and validated.", str(Path(backup).resolve()))

    def rollback(self, backup: str | Path) -> AdminResult:
        result = self.manager.rollback(backup)
        return AdminResult("rollback", bool(result.get("valid")), "Rollback completed and validated.", str(Path(backup).resolve()))

    def reset(self, confirmation: str, backup_before_reset: bool = True) -> AdminResult:
        """Reset operational state through an externally recoverable snapshot.

        The confirmation is an operation token, not an authentication system.
        Authorization belongs to the external administrative execution context.
        """
        if confirmation != RESET_CONFIRMATION:
            raise LifecycleError(f"Reset requires the exact confirmation token: {RESET_CONFIRMATION!r}")

        artifact = self.manager.backup(label="pre-reset") if backup_before_reset else None
        # The current application reset endpoint is intentionally not called.
        # The dedicated tool owns reset and must use the same lifecycle manager
        # boundary. Database-specific zero-state work is supplied separately by
        # the administrative reset implementation once its operational table
        # inventory is finalized.
        raise LifecycleError(
            "Reset orchestration is reserved for the dedicated administrative "
            "tool; database zero-state mutation has not been enabled by this facade."
        )

    def purge(self, confirmation: str) -> AdminResult:
        if confirmation != "PURGE DAIRYOS DATA":
            raise LifecycleError("Permanent purge requires the exact confirmation token.")
        artifact = create_external_purge_backup(self.manager)
        purge_data_after_backup(self.manager, create_backup=False)
        return AdminResult("purge", True, "Data root purged after external backup.", str(artifact))

    def uninstall(self, purge: bool = False, confirmation: str | None = None) -> AdminResult:
        mode = UninstallMode.PURGE_DATA if purge else UninstallMode.KEEP_DATA
        self.manager.uninstall(mode=mode, confirmation=confirmation)
        return AdminResult("uninstall", True, "Uninstall completed.")
