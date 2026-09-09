"""Windows scheduled backup worker for the packaged DairyOS appliance."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

from sqlalchemy.engine import URL

from dairyos.data.database.automatic_backups import run_automatic_backup
from dairyos.windows.appliance_database import prepare_database
from dairyos.windows.private_postgres import (
    persisted_cluster_is_running,
    stop as stop_private_postgres,
)


LOG = logging.getLogger("dairyos.windows.backup_task")
TASK_NAME = "DairyOS-Automatic-Backup"
INTERVAL_HOURS = 6
BACKUP_EXE_NAME = "DairyOSBackup.exe"


class BackupTaskError(RuntimeError):
    """Raised when DairyOS cannot provision or execute automatic backups."""


def packaged_backup_executable() -> Path:
    override = os.environ.get("DAIRYOS_BACKUP_EXECUTABLE", "").strip()
    if override:
        return Path(override).expanduser().resolve()

    if bool(getattr(sys, "frozen", False)):
        return Path(sys.executable).resolve().parent / BACKUP_EXE_NAME

    return Path(sys.executable).resolve()


def _task_command() -> str:
    if bool(getattr(sys, "frozen", False)):
        executable = packaged_backup_executable()
        if not executable.is_file():
            raise BackupTaskError(
                f"Packaged DairyOS backup worker is missing: {executable}"
            )
        return f'"{executable}"'

    return f'"{Path(sys.executable).resolve()}" -m dairyos.windows.backup_task'


def _scheduled_task_action() -> tuple[str, str] | None:
    """Return the structured Task Scheduler action, or None when absent."""

    if os.name != "nt":
        return (str(packaged_backup_executable()), "")

    query = subprocess.run(
        ["schtasks.exe", "/Query", "/TN", TASK_NAME, "/XML"],
        capture_output=True,
        text=True,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if query.returncode != 0:
        return None

    try:
        root = ET.fromstring(query.stdout)
    except ET.ParseError as exc:
        raise BackupTaskError(
            "Automatic DairyOS backup task exists but its Task Scheduler "
            "definition could not be parsed. Repair or reinstall DairyOS."
        ) from exc

    namespace = {"task": "http://schemas.microsoft.com/windows/2004/02/mit/task"}
    command = root.findtext(".//task:Exec/task:Command", default="", namespaces=namespace)
    arguments = root.findtext(".//task:Exec/task:Arguments", default="", namespaces=namespace)
    return (str(command or "").strip(), str(arguments or "").strip())


def scheduled_backup_task_exists() -> bool:
    """Return whether the installer task exists with the exact safe action."""

    if os.name != "nt":
        return True

    action = _scheduled_task_action()
    if action is None:
        return False

    executable, arguments = action
    expected = packaged_backup_executable()
    try:
        actual = Path(executable).expanduser().resolve()
    except (OSError, RuntimeError):
        return False

    return actual == expected and arguments == ""


def ensure_scheduled_backup_task(*, run_immediately: bool = False) -> None:
    """Verify the installer-provisioned six-hour backup schedule.

    Task creation is an installation-time privileged operation. Normal DairyOS
    startup is intentionally non-elevated and must never attempt task creation.
    The application verifies both task existence and its structured executable
    action so a malformed Program Files split cannot qualify as farm data
    protection.
    """

    if os.name != "nt":
        return

    action = _scheduled_task_action()
    if action is None:
        raise BackupTaskError(
            "Automatic DairyOS backups are not provisioned. "
            "Repair or reinstall DairyOS using the Windows installer."
        )

    executable, arguments = action
    expected = packaged_backup_executable()
    try:
        actual = Path(executable).expanduser().resolve()
    except (OSError, RuntimeError) as exc:
        raise BackupTaskError(
            "Automatic DairyOS backup task has an invalid executable path. "
            "Repair or reinstall DairyOS."
        ) from exc

    if actual != expected or arguments:
        raise BackupTaskError(
            "Automatic DairyOS backup task is misconfigured. "
            f"Expected executable '{expected}' with no arguments, got "
            f"executable '{executable}' and arguments '{arguments}'. "
            "Repair or reinstall DairyOS."
        )

    if run_immediately:
        LOG.info(
            "Automatic DairyOS backup task verified; first backup will run "
            "on the installer-provisioned schedule."
        )

def _ordinary_database_url(database) -> str:
    return URL.create(
        "postgresql+psycopg",
        username=database.user,
        password=database.password or None,
        host=database.host,
        port=database.port,
        database=database.database,
    ).render_as_string(hide_password=False)


def run_backup_once() -> int:
    """Create one backup using only the read-only backup database identity.

    The worker may start the private cluster when DairyOS is closed, but must
    never stop a cluster that was already running for an active desktop/backend
    session before the backup began.
    """

    private = None
    cluster_was_running = False
    try:
        cluster_was_running = persisted_cluster_is_running()
        database = prepare_database(postgres_timeout=60.0)
        private = database.private_postgres
        database_url = database.backup_database_url or _ordinary_database_url(database)

        result = run_automatic_backup(database_url)
        LOG.info(
            "DairyOS automatic backup completed: primary=%s mirror=%s monthly=%s redundant=%s",
            result.primary,
            result.mirror,
            result.monthly_primary,
            result.physically_redundant,
        )
        return 0
    except Exception:
        LOG.exception("DairyOS automatic backup failed")
        return 1
    finally:
        if private is not None and not cluster_was_running:
            try:
                stop_private_postgres(private)
            except Exception:
                LOG.exception("Failed to stop private PostgreSQL started by scheduled backup")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return run_backup_once()


if __name__ == "__main__":
    raise SystemExit(main())
