from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path


PROGRAM_DATA = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "DairyOS"
ENV_FILE = PROGRAM_DATA / "dairyos.env"
LOG_FILE = PROGRAM_DATA / "logs" / "postgresql.log"


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key:
            os.environ[key] = value


def _pg_paths() -> tuple[Path, Path]:
    pg_bin = Path(os.environ["DAIRYOS_PG_BIN"])
    pg_data = Path(os.environ["DAIRYOS_PG_DATA"])
    return pg_bin, pg_data


def _run_checked(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=True,
        text=True,
        capture_output=True,
        env=env,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _ensure_postgres() -> None:
    pg_bin, pg_data = _pg_paths()
    pg_ctl = pg_bin / "pg_ctl.exe"
    psql = pg_bin / "psql.exe"
    createdb = pg_bin / "createdb.exe"

    PROGRAM_DATA.joinpath("logs").mkdir(parents=True, exist_ok=True)
    if not pg_data.exists() or not (pg_data / "PG_VERSION").exists():
        raise RuntimeError("DairyOS PostgreSQL data directory is not initialized.")

    status = subprocess.run(
        [str(pg_ctl), "status", "-D", str(pg_data)],
        text=True,
        capture_output=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if status.returncode != 0:
        _run_checked(
            [
                str(pg_ctl),
                "start",
                "-D",
                str(pg_data),
                "-l",
                str(LOG_FILE),
                "-w",
                "-o",
                f"-p {os.environ.get('DAIRYOS_DB_PORT', '5432')}",
            ]
        )

    env = dict(os.environ)
    env["PGPASSWORD"] = os.environ["DAIRYOS_DB_PASSWORD"]
    host = os.environ.get("DAIRYOS_DB_HOST", "127.0.0.1")
    port = os.environ.get("DAIRYOS_DB_PORT", "5432")
    user = os.environ.get("DAIRYOS_DB_USER", "postgres")
    database = os.environ.get("DAIRYOS_DB_NAME", "dairyos")

    probe = subprocess.run(
        [
            str(psql),
            "-h",
            host,
            "-p",
            port,
            "-U",
            user,
            "-d",
            "postgres",
            "-tAc",
            f"SELECT 1 FROM pg_database WHERE datname = '{database}'",
        ],
        text=True,
        capture_output=True,
        env=env,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if probe.returncode != 0:
        raise RuntimeError(probe.stderr.strip() or "Unable to connect to PostgreSQL.")
    if probe.stdout.strip() != "1":
        _run_checked(
            [str(createdb), "-h", host, "-p", port, "-U", user, database],
            env=env,
        )


def initialize_only() -> None:
    _load_env_file(ENV_FILE)
    _ensure_postgres()
    from dairyos.data.database.initialize import initialize_database

    initialize_database()


def launch() -> None:
    _load_env_file(ENV_FILE)
    _ensure_postgres()

    import uvicorn

    threading.Thread(
        target=lambda: (time.sleep(2), webbrowser.open("http://127.0.0.1:8000/")),
        daemon=True,
    ).start()
    uvicorn.run(
        "dairyos.app:app",
        host="127.0.0.1",
        port=int(os.environ.get("DAIRYOS_APP_PORT", "8000")),
        log_level="info",
    )


if __name__ == "__main__":
    if "--initialize-only" in sys.argv:
        initialize_only()
    else:
        launch()
