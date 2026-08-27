"""Generic bundled-component detection and version policy for DairyOS."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
import subprocess
from typing import Callable


class ComponentError(RuntimeError):
    """Base error for bundled-component management."""


class ComponentVersionUnknown(ComponentError):
    """Raised when an installed component cannot be version-identified."""


class ComponentAction(str, Enum):
    FRESH_INSTALL = "fresh-install"
    RETAIN_EXISTING = "retain-existing"
    UPDATE = "update"
    RETAIN_NEWER = "retain-newer"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ComponentSpec:
    """Definition of a component DairyOS may provision."""

    key: str
    display_name: str
    bundled_version: str
    detect_version: Callable[[], str | None]
    install: Callable[[], None]
    update: Callable[[], None] | None = None
    is_compatible: Callable[[str], bool] | None = None


@dataclass(frozen=True)
class ComponentInspection:
    """Observed installed/bundled versions and the resulting safe action."""

    key: str
    display_name: str
    installed_version: str | None
    bundled_version: str
    action: ComponentAction
    notification: str


_VERSION_RE = re.compile(r"^\s*v?(\d+(?:\.\d+){0,3})(?:[-+].*)?\s*$", re.IGNORECASE)


def normalize_version(value: str) -> tuple[int, ...]:
    """Normalize a simple numeric semantic version for comparison."""
    match = _VERSION_RE.match(value)
    if not match:
        raise ComponentVersionUnknown(
            f"Unsupported component version format: {value!r}"
        )

    return tuple(int(part) for part in match.group(1).split("."))


def compare_versions(left: str, right: str) -> int:
    """Return -1, 0, or 1 for left < right, ==, or > right."""
    a = normalize_version(left)
    b = normalize_version(right)

    width = max(len(a), len(b))
    a += (0,) * (width - len(a))
    b += (0,) * (width - len(b))

    return (a > b) - (a < b)


def inspect_component(spec: ComponentSpec) -> ComponentInspection:
    """Detect an installed component and determine the safe action."""
    installed = spec.detect_version()

    if installed is None:
        return ComponentInspection(
            key=spec.key,
            display_name=spec.display_name,
            installed_version=None,
            bundled_version=spec.bundled_version,
            action=ComponentAction.FRESH_INSTALL,
            notification=(
                f"{spec.display_name} is not installed. "
                f"DairyOS bundled version {spec.bundled_version} will be installed."
            ),
        )

    if spec.is_compatible is not None and not spec.is_compatible(installed):
        return ComponentInspection(
            key=spec.key,
            display_name=spec.display_name,
            installed_version=installed,
            bundled_version=spec.bundled_version,
            action=ComponentAction.BLOCKED,
            notification=(
                f"{spec.display_name} version {installed} is installed, but it is "
                "not compatible with this DairyOS release. Installation is blocked."
            ),
        )

    comparison = compare_versions(installed, spec.bundled_version)

    if comparison < 0:
        if spec.update is None:
            action = ComponentAction.BLOCKED
            message = (
                f"{spec.display_name} installed version {installed} is older than "
                f"the bundled version {spec.bundled_version}, but no validated "
                "automatic upgrade path is available. Existing version will be "
                "left untouched."
            )
        else:
            action = ComponentAction.UPDATE
            message = (
                f"{spec.display_name} already installed. "
                f"Installed version: {installed}. "
                f"DairyOS bundled version: {spec.bundled_version}. "
                f"The newer DairyOS version {spec.bundled_version} will be retained."
            )
    elif comparison == 0:
        action = ComponentAction.RETAIN_EXISTING
        message = (
            f"{spec.display_name} already installed. "
            f"Installed version: {installed}. "
            f"DairyOS bundled version: {spec.bundled_version}. "
            "The existing installation will be retained."
        )
    else:
        action = ComponentAction.RETAIN_NEWER
        message = (
            f"{spec.display_name} already installed. "
            f"Installed version: {installed}. "
            f"DairyOS bundled version: {spec.bundled_version}. "
            f"The newer installed version {installed} will be retained."
        )

    return ComponentInspection(
        key=spec.key,
        display_name=spec.display_name,
        installed_version=installed,
        bundled_version=spec.bundled_version,
        action=action,
        notification=message,
    )


def apply_component(spec: ComponentSpec) -> ComponentInspection:
    """Apply a safe component action after inspection."""
    inspection = inspect_component(spec)

    if inspection.action is ComponentAction.FRESH_INSTALL:
        spec.install()
    elif inspection.action is ComponentAction.UPDATE:
        if spec.update is None:
            raise ComponentError(
                f"{spec.display_name} requires an upgrade but no upgrade handler exists."
            )
        spec.update()
    elif inspection.action is ComponentAction.BLOCKED:
        raise ComponentError(inspection.notification)

    return inspection


def windows_program_version(executable: str) -> str | None:
    """Read a Windows executable's file-product version using PowerShell."""
    if not executable:
        return None

    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            (
                "$v=(Get-Item -LiteralPath $args[0]).VersionInfo.FileVersion;"
                "if($v){$v}"
            ),
            executable,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )

    value = result.stdout.strip()
    return value or None