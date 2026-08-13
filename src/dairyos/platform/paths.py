"""Where DairyOS keeps a farm's data.

Until now the two JSON-backed repositories wrote to the relative path
``data/storage/``, which resolves against the *current working directory*. That
is survivable for a developer who always starts the server from the repository
root, and wrong in every other case: a packaged application launched from a
desktop shortcut would scatter farm records wherever the shell happened to be,
and an uninstaller removing the program directory could take the farm's data
with it.

This module resolves one data root, outside the installation, per platform:

===========  ==========================================
Windows      ``%LOCALAPPDATA%\\DairyOS``
macOS        ``~/Library/Application Support/DairyOS``
Linux        ``$XDG_DATA_HOME/DairyOS`` or ``~/.local/share/DairyOS``
===========  ==========================================

``DAIRYOS_DATA_DIR`` overrides it entirely, which is how tests, a portable
install on a USB drive, and a farm keeping data on a NAS all work without
special cases.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


APPLICATION_NAME = "DairyOS"

DATA_DIR_ENV_VAR = "DAIRYOS_DATA_DIR"


def _platform_data_root() -> Path:
    """The conventional per-user data directory for this operating system."""

    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if base:
            return Path(base) / APPLICATION_NAME
        return Path.home() / "AppData" / "Local" / APPLICATION_NAME

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APPLICATION_NAME

    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / APPLICATION_NAME

    return Path.home() / ".local" / "share" / APPLICATION_NAME


def data_root(create: bool = True) -> Path:
    """The root of this installation's farm data.

    ``DAIRYOS_DATA_DIR`` wins if set. The directory is created on demand so no
    caller has to decide whether it is the one responsible for making it.
    """

    override = os.environ.get(DATA_DIR_ENV_VAR)
    root = Path(override).expanduser() if override else _platform_data_root()

    if create:
        root.mkdir(parents=True, exist_ok=True)

    return root


def storage_dir(create: bool = True) -> Path:
    """Where the JSON-backed operational repositories persist."""

    path = data_root(create=create) / "storage"

    if create:
        path.mkdir(parents=True, exist_ok=True)

    return path


def storage_path(filename: str, create: bool = True) -> Path:
    """Resolve one file inside the storage directory."""

    return storage_dir(create=create) / filename


LEGACY_STORAGE_DIR = Path("data") / "storage"


def resolve_storage_file(filename: str) -> Path:
    """Where a JSON repository should read and write ``filename``.

    Existing farms keep their data. If the managed location has no such file
    but the old working-directory-relative ``data/storage/`` one does, that
    path is returned unchanged, so upgrading DairyOS never orphans records a
    farm already has. Nothing is copied or moved: a silent migration that goes
    wrong is worse than an explicit one that is deferred.

    A fresh installation, having neither, gets the managed location.
    """

    managed = storage_dir(create=False) / filename

    if managed.exists():
        return managed

    legacy = LEGACY_STORAGE_DIR / filename
    if legacy.exists():
        return legacy

    return storage_path(filename)


def backups_dir(create: bool = True) -> Path:
    """Where versioned backups are written."""

    path = data_root(create=create) / "backups"

    if create:
        path.mkdir(parents=True, exist_ok=True)

    return path


def logs_dir(create: bool = True) -> Path:
    path = data_root(create=create) / "logs"

    if create:
        path.mkdir(parents=True, exist_ok=True)

    return path


def config_path(create: bool = True) -> Path:
    """The farm configuration file written by the first-run wizard."""

    return data_root(create=create) / "config.json"


def describe() -> dict[str, str]:
    """Resolved locations, for health checks and support questions.

    Directories are reported without being created, so asking where data lives
    never has the side effect of putting a directory there.
    """

    return {
        "data_root": str(data_root(create=False)),
        "storage": str(storage_dir(create=False)),
        "backups": str(backups_dir(create=False)),
        "logs": str(logs_dir(create=False)),
        "config": str(config_path(create=False)),
        "overridden_by_env": str(DATA_DIR_ENV_VAR in os.environ),
        "legacy_storage_in_use": str(
            not (storage_dir(create=False)).exists()
            and LEGACY_STORAGE_DIR.exists()
        ),
    }
