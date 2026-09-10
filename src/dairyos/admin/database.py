"""Canonical private-database ownership for protected DairyOS lifecycle work."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import socket
import sys

from dairyos.lifecycle.manager import LifecycleError, LifecycleManager


@dataclass
class AdminDatabaseLease:
    manager: LifecycleManager
    private_postgres: object | None = None
    stop_on_close: bool = False
    _closed: bool = False

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self.stop_on_close and self.private_postgres is not None:
            from dairyos.windows.private_postgres import stop

            stop(self.private_postgres)


def acquire_admin_database(
    installation_root: str | Path,
    *,
    data_root: str | Path | None = None,
) -> AdminDatabaseLease:
    """Resolve the protected lifecycle service to packaged DairyOS authority."""

    if not bool(getattr(sys, "frozen", False)):
        manager = LifecycleManager(
            installation_root,
            data_root=data_root,
            database_url=os.environ.get("DAIRYOS_DATABASE_URL"),
        )
        return AdminDatabaseLease(manager=manager)

    from dairyos.windows.appliance_database import prepare_database

    was_running = _private_database_running()
    database = prepare_database()

    if database.private_postgres is None or not database.migration_database_url:
        raise LifecycleError(
            "DairyOS could not resolve the private PostgreSQL database authority."
        )

    manager = LifecycleManager(
        installation_root,
        data_root=data_root,
        database_url=database.migration_database_url,
    )
    return AdminDatabaseLease(
        manager=manager,
        private_postgres=database.private_postgres,
        stop_on_close=not was_running,
    )


def _private_database_running() -> bool:
    from dairyos.windows.private_postgres import postgres_data_root, runtime_state_path

    data_root = postgres_data_root()
    if not (data_root / "postmaster.pid").is_file():
        return False

    state_path = runtime_state_path()
    if not state_path.is_file():
        return False

    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        host = str(state.get("host") or "127.0.0.1")
        port = int(state["port"])
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return False

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        try:
            sock.connect((host, port))
        except OSError:
            return False
    return True
