"""Runtime mode selection shared by the DairyOS server and adapters."""

from __future__ import annotations

import os
import sys
from enum import StrEnum

RUNTIME_MODE_ENV = "DAIRYOS_RUNTIME_MODE"


class RuntimeMode(StrEnum):
    DEVELOPMENT = "development"
    WINDOWS_APPLIANCE = "windows-appliance"
    HOSTED = "hosted"
    BROWSER_CLIENT = "browser-client"


class RuntimeModeError(RuntimeError):
    """Raised when a runtime mode is unknown or incompatible with the entrypoint."""


def resolve_runtime_mode(
    value: str | None = None,
    *,
    frozen: bool | None = None,
    platform: str | None = None,
) -> RuntimeMode:
    """Resolve an explicit mode, retaining the established development default."""
    is_frozen = bool(getattr(sys, "frozen", False)) if frozen is None else frozen
    current_platform = sys.platform if platform is None else platform
    if is_frozen and current_platform != "win32":
        raise RuntimeModeError(
            "A frozen DairyOS executable requires the windows-appliance "
            "runtime mode on Windows."
        )

    configured = value if value is not None else os.environ.get(RUNTIME_MODE_ENV)
    if configured is not None and configured.strip():
        try:
            mode = RuntimeMode(configured.strip().lower())
        except ValueError as exc:
            valid = ", ".join(mode.value for mode in RuntimeMode)
            raise RuntimeModeError(
                f"Invalid {RUNTIME_MODE_ENV} value. Expected one of: {valid}."
            ) from exc
        if is_frozen and mode is not RuntimeMode.WINDOWS_APPLIANCE:
            raise RuntimeModeError(
                "A frozen DairyOS executable cannot override its "
                "windows-appliance runtime mode."
            )
        if mode is RuntimeMode.WINDOWS_APPLIANCE and current_platform != "win32":
            raise RuntimeModeError(
                "The windows-appliance runtime mode is supported only on Windows."
            )
        return mode

    if is_frozen:
        return RuntimeMode.WINDOWS_APPLIANCE
    environment = os.environ.get("DAIRYOS_ENV", "development").strip().lower()
    if environment in {"production", "staging", "preprod"}:
        return (
            RuntimeMode.WINDOWS_APPLIANCE
            if current_platform == "win32"
            else RuntimeMode.HOSTED
        )
    return RuntimeMode.DEVELOPMENT


def require_server_mode(mode: RuntimeMode) -> None:
    if mode is RuntimeMode.BROWSER_CLIENT:
        raise RuntimeModeError(
            "browser-client is a frontend deployment mode and cannot start the DairyOS server."
        )
