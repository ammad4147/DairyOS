"""Select platform startup adapters without importing them into shared entrypoints."""

from __future__ import annotations

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
        raise RuntimeStartupError(
            "Hosted startup is not ready: a platform-neutral migration adapter "
            "must be configured before the hosted server can start."
        )
    raise RuntimeStartupError(
        f"Production startup gates are not available for runtime mode '{mode.value}'."
    )


def record_successful_start(mode: RuntimeMode) -> Path | None:
    """Record install health only for the Windows appliance adapter."""
    if mode is not RuntimeMode.WINDOWS_APPLIANCE:
        return None

    from dairyos.windows.startup_integrity import record_successful_start as record

    return record()
