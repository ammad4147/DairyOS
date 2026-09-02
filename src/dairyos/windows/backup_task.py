"""Windows scheduled backup worker for the packaged DairyOS appliance."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import subprocess
import sys

from dairyos.data.database.automatic_backups import run_automatic_backup
from dairyos.windows.appliance_database import apply_database_environment, prepare_database
from dairyos.windows.private_postgres import stop as stop_private_postgres


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


def ensure_scheduled_backup_task(*, run_immediately: bool = False) -> None:
    """Create/update the unskippable six-hour Windows backup schedule."""

    if os.name != "nt":
        return

    command = _task_command()
    create = subprocess.run(
        [
            "schtasks.exe",
            "/Create",
            "/F",
            "/TN",
            TASK_NAME,
            "/SC",
            "HOURLY",
            "/MO",
            str(INTERVAL_HOURS),
            "/ST",
            "00:00",
            "/RL",
            "LIMITED",
            "/TR",
            command,
        ],
        capture_output=True,
        text=True,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if create.returncode != 0:
        detail = create.stderr.strip() or create.stdout.strip() or "schtasks /Create failed"
        raise BackupTaskError(f"Could not provision automatic DairyOS backups: {detail}")

    if run_immediately:
        started = subprocess.run(
            ["schtasks.exe", "/Run", "/TN", TASK_NAME],
            capture_output=True,
            text=True,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if started.returncode != 0:
            detail = started.stderr.strip() or started.stdout.strip() or "schtasks /Run failed"
            raise BackupTaskError(f"Could not start the first DairyOS backup: {detail}")


def run_backup_once() -> int:
    """Start the managed database if needed, create a backup, then stop it."""

    database = None
    private = None
    try:
        database = prepare_database(postgres_timeout=60.0)
        private = database.private_postgres
        apply_database_environment(database)

        from dairyos.data.database.session import _build_database_url

        database_url = _build_database_url()
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
        if private is not None:
            try:
                stop_private_postgres(private)
            except Exception:
                LOG.exception("Failed to stop private PostgreSQL after scheduled backup")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return run_backup_once()


if __name__ == "__main__":
    raise SystemExit(main())
