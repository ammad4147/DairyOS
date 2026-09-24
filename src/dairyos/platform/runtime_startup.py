"""Select platform startup adapters without importing them into shared entrypoints."""

from __future__ import annotations

import os
from pathlib import Path

from dairyos.platform.runtime_mode import RuntimeMode


class RuntimeStartupError(RuntimeError):
    """Raised when the selected deployment mode lacks a required startup adapter."""


def run_production_startup_gates(mode: RuntimeMode) -> None:
    """Run the schema gate owned by the selected application runtime."""
    if mode is RuntimeMode.WINDOWS_APPLIANCE:
        from dairyos.windows.migrations import migrate_if_needed

        migrate_if_needed()
        return
    if mode is RuntimeMode.HOSTED:
        if not os.getenv("DAIRYOS_EMAIL_SECRET"):
            raise RuntimeStartupError(
                "Hosted mode requires DAIRYOS_EMAIL_SECRET, a stable secret used only to protect saved SMTP credentials."
            )
        from dairyos.platform.hosted_migrations import migrate_hosted_database

        try:
            migrate_hosted_database()
        except Exception as exc:
            raise RuntimeStartupError(str(exc)) from exc
        return
    raise RuntimeStartupError(
        f"Production startup gates are not available for runtime mode '{mode.value}'."
    )


def record_successful_start(mode: RuntimeMode) -> Path | None:
    """Record install health only for the Windows appliance adapter."""
    if mode is not RuntimeMode.WINDOWS_APPLIANCE:
        return None

    from dairyos.windows.startup_integrity import record_successful_start as record

    return record()
