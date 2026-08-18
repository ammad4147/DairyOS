"""DairyOS installation, upgrade, recovery, and uninstallation lifecycle."""

from .manager import (
    LifecycleError,
    LifecycleManager,
    LifecycleValidationError,
    UninstallMode,
)

__all__ = [
    "LifecycleError",
    "LifecycleManager",
    "LifecycleValidationError",
    "UninstallMode",
]
