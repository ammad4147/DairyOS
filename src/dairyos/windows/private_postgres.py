"""Private PostgreSQL runtime management for the DairyOS Windows appliance."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time

from dairyos.platform import paths
from dairyos.windows.components import compare_versions


class PrivatePostgreSQLError(RuntimeError):
    """Raised when the DairyOS private PostgreSQL runtime cannot be used."""


@dataclass(frozen=True)
class PrivatePostgreSQLConfig:
    runtime_root: Path
    data_root: Path
    host: str
    port: int
    database: str
    user: str
    bundled_version: str


@dataclass(frozen=True)
class PrivatePostgreSQLStatus:
    installed: bool
    running: bool
    version: str | None
    data_root: Path
    port: int | None


RUNTIME_STATE_FILENAME = "runtime.json"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_DATABASE = "dairyos"
DEFAULT_USER = "dairyos_admin"
_VERSION_RE = re.compile(r"PostgreSQL\)?\s+([0-9]+(?:\.[0-9]+){1,3})", re.IGNORECASE)


def runtime_root() -> Path:
    """Return the PostgreSQL runtime shipped with the DairyOS bundle.

    A frozen DairyOS appliance owns the runtime beside its executable. Machine
    or inherited environment values must never redirect an installed
    DairyOS.exe to a stale or unrelated PostgreSQL tree after reinstall.
    Development/source runs retain the existing explicit override seams.
    """
    if getattr(sys, "frozen", False):
        return (
            Path(sys.executable).resolve().parent
            / "runtime"
            / "PostgreSQL"
        )

    override = os.environ.get("DAIRYOS_PRIVATE_POSTGRES_RUNTIME")
    if override:
        return Path(override).expanduser().resolve()

    install_root = os.environ.get("DAIRYOS_INSTALL_ROOT")
    if install_root:
        return (
            Path(install_root).expanduser().resolve()
            / "runtime"
            / "PostgreSQL"
        )

    return Path(__file__).resolve().parents[3] / "runtime" / "PostgreSQL"


def postgres_data_root() -> Path:
    """Return the persistent private PostgreSQL cluster location."""
    override = os.environ.get("DAIRYOS_PRIVATE_POSTGRES_DATA")
    if override:
        return Path(override).expanduser().resolve()

    return paths.data_root(create=True) / "postgres" / "data"


def runtime_state_path() -> Path:
    return postgres_data_root().parent / RUNTIME_STATE_FILENAME


def bundled_version() -> str:
    """Return the PostgreSQL version declared by the DairyOS bundle."""
    frozen = bool(getattr(sys, "frozen", False))
    if not frozen:
        override = os.environ.get(
            "DAIRYOS_PRIVATE_POSTGRES_VERSION",
            "",
        ).strip()
        if override:
            return override

    version_file = runtime_root().parent / "postgresql.version"
    if not version_file.is_file():
        if frozen:
            raise PrivatePostgreSQLError(
                "The bundled PostgreSQL version marker is missing: "
                f"{version_file}"
            )
    else:
        value = version_file.read_text(encoding="utf-8").strip()
        if value:
            return value
        if frozen:
            raise PrivatePostgreSQLError(
                "The bundled PostgreSQL version marker is empty: "
                f"{version_file}"
            )

    detected = detect_installed_version()
    if detected:
        return detected

    raise PrivatePostgreSQLError(
        "The bundled PostgreSQL version could not be determined."
    )


def _binary(name: str) -> Path:
    root = runtime_root()
    candidates = (
        root / "bin" / name,
        root / name,
    )

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise PrivatePostgreSQLError(
        f"Bundled PostgreSQL executable was not found: {name} under {root}"
    )


def _run(
    command: list[str],
    *,
    check: bool = True,
    timeout: float = 30.0,
    capture: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        if capture:
            result = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=timeout,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                env=env,
            )
        else:
            result = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=timeout,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                env=env,
            )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PrivatePostgreSQLError(
            f"Failed to execute PostgreSQL command: {' '.join(command)}"
        ) from exc

    if check and result.returncode != 0:
        details = " ".join(
            value.strip()
            for value in (
                getattr(result, "stdout", ""),
                getattr(result, "stderr", ""),
            )
            if value and value.strip()
        )
        raise PrivatePostgreSQLError(
            f"PostgreSQL command failed ({result.returncode}): "
            f"{' '.join(command)} {details}".strip()
        )

    return result

def detect_installed_version() -> str | None:
    """Read the version from the PostgreSQL executable in the private bundle."""
    try:
        result = _run(
            [str(_binary("postgres.exe")), "--version"],
            check=False,
            timeout=10,
        )
    except PrivatePostgreSQLError:
        return None

    output = f"{result.stdout}\n{result.stderr}"
    match = _VERSION_RE.search(output)
    return match.group(1) if match else None


def _is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        try:
            sock.connect((host, port))
            return True
        except OSError:
            return False


def _choose_port(host: str = DEFAULT_HOST) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def _pid_file(data_root: Path) -> Path:
    return data_root / "postmaster.pid"


def _read_state() -> dict[str, object]:
    path = runtime_state_path()
    if not path.is_file():
        return {}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PrivatePostgreSQLError(
            f"Private PostgreSQL runtime state is invalid: {path}"
        ) from exc

    if not isinstance(payload, dict):
        raise PrivatePostgreSQLError(
            f"Private PostgreSQL runtime state is not an object: {path}"
        )

    return payload


def _write_state(payload: dict[str, object]) -> None:
    path = runtime_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")

    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _configured_port() -> int | None:
    state = _read_state()
    value = state.get("port")

    if value is None:
        return None

    try:
        port = int(value)
    except (TypeError, ValueError) as exc:
        raise PrivatePostgreSQLError(
            f"Persisted private PostgreSQL port is invalid: {value!r}"
        ) from exc

    if not 1 <= port <= 65535:
        raise PrivatePostgreSQLError(
            f"Persisted private PostgreSQL port is outside the valid range: {port}"
        )

    return port


def _write_postgresql_conf(
    data_root: Path,
    host: str,
    port: int,
) -> None:
    conf = data_root / "postgresql.conf"

    settings = [
        f"listen_addresses = '{host}'",
        f"port = {port}",
        "password_encryption = 'scram-sha-256'",
        "logging_collector = on",
        "log_destination = 'stderr'",
        "log_directory = 'log'",
        "log_filename = 'dairyos-%Y-%m-%d_%H%M%S.log'",
    ]

    conf.write_text(
        "\n".join(settings) + "\n",
        encoding="utf-8",
    )


def _write_pg_hba_conf(
    data_root: Path,
    user: str,
    database: str,
) -> None:
    hba = data_root / "pg_hba.conf"

    hba.write_text(
        "\n".join(
            [
                "# Managed by DairyOS. Loopback-only private database.",
                f"local   all         {user}                  trust",
                f"host    all         {user}   127.0.0.1/32   trust",
                f"host    all         {user}   ::1/128        trust",
                "local   all         all                    reject",
                "host    all         all    0.0.0.0/0       reject",
                "host    all         all    ::0/0           reject",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def initialize_cluster(
    *,
    data_root: Path,
    user: str,
) -> None:
    """Initialize only a genuinely empty private PostgreSQL cluster."""
    if data_root.exists():
        if any(data_root.iterdir()):
            raise PrivatePostgreSQLError(
                f"Cannot initialize PostgreSQL: data directory is not empty: {data_root}"
            )

        # On Windows, initdb must be allowed to create the cluster directory
        # itself so it can apply the required ownership/ACLs. An empty directory
        # pre-created by DairyOS can inherit permissions that initdb cannot
        # tighten, producing a first-start "Permission denied" failure.
        try:
            data_root.rmdir()
        except OSError as exc:
            raise PrivatePostgreSQLError(
                f"Cannot prepare empty PostgreSQL data directory for initdb: {data_root}"
            ) from exc

    data_root.parent.mkdir(parents=True, exist_ok=True)

    _run(
        [
            str(_binary("initdb.exe")),
            "-D",
            str(data_root),
            "--username",
            user,
            "--auth-local",
            "trust",
            "--auth-host",
            "trust",
            "--no-locale",
            "--encoding",
            "UTF8",
        ],
        timeout=120,
    )


def _wait_for_server(
    host: str,
    port: int,
    timeout: float = 30.0,
) -> None:
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if _is_port_open(host, port):
            return
        time.sleep(0.25)

    raise PrivatePostgreSQLError(
        f"Private PostgreSQL did not become available on {host}:{port}."
    )


def _psql(
    *,
    host: str,
    port: int,
    database: str,
    user: str,
    sql: str,
    timeout: float = 30.0,
) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            str(_binary("psql.exe")),
            "-w",
            "-h",
            host,
            "-p",
            str(port),
            "-U",
            user,
            "-d",
            database,
            "-v",
            "ON_ERROR_STOP=1",
            "-tAc",
            sql,
        ],
        timeout=timeout,
    )


def _ensure_role_and_database(
    *,
    host: str,
    port: int,
    database: str,
    user: str,
) -> None:
    """Ensure the DairyOS database exists without replacing existing data."""
    database_exists = _psql(
        host=host,
        port=port,
        database="postgres",
        user=user,
        sql=(
            "SELECT 1 FROM pg_database "
            "WHERE datname = 'dairyos';"
        ),
    ).stdout.strip()

    if database_exists != "1":
        _run(
            [
                str(_binary("createdb.exe")),
                "-w",
                "-h",
                host,
                "-p",
                str(port),
                "-U",
                user,
                "-O",
                user,
                database,
            ],
            timeout=30,
        )

def start(
    *,
    host: str = DEFAULT_HOST,
    port: int | None = None,
    database: str = DEFAULT_DATABASE,
    user: str = DEFAULT_USER,
    timeout: float = 30.0,
) -> PrivatePostgreSQLConfig:
    """Start or initialize the persistent private DairyOS PostgreSQL cluster."""
    data_root = postgres_data_root()
    data_root.parent.mkdir(parents=True, exist_ok=True)
    runtime_version = detect_installed_version()
    expected_version = bundled_version()
    if runtime_version is None:
        raise PrivatePostgreSQLError(
            "The bundled PostgreSQL runtime is missing or cannot report its version."
        )

    # The application bundle owns this runtime. A different system PostgreSQL
    # installation is not considered a substitute.
    if compare_versions(runtime_version, expected_version) != 0:
        raise PrivatePostgreSQLError(
            "Bundled PostgreSQL version mismatch: "
            f"binary={runtime_version}, declared={expected_version}."
        )
    existing_state = _read_state()
    cluster_exists = data_root.exists() and any(data_root.iterdir())
    if cluster_exists:
        cluster_user = str(existing_state.get("user") or "dairyos")
    else:
        cluster_user = user
    persisted_port = _configured_port()
    selected_port = port or persisted_port or _choose_port(host)
    if persisted_port is not None and port is not None and persisted_port != port:
        raise PrivatePostgreSQLError(
            f"Private PostgreSQL cluster already belongs to port {persisted_port}; "
            f"refusing to silently move it to {port}."
        )

    if not data_root.exists() or not any(data_root.iterdir()):
        initialize_cluster(
            data_root=data_root,
            user=cluster_user,
        )

    _write_postgresql_conf(data_root, host, selected_port)
    _write_pg_hba_conf(data_root, cluster_user, database)
    pg_ctl = _binary("pg_ctl.exe")
    pid_path = _pid_file(data_root)

    if pid_path.is_file() and not _is_port_open(host, selected_port):
        # A postmaster PID file can survive an abnormal termination.
        # pg_ctl status return code 3 means the cluster is not running.
        # In that specific case the PID file is stale and the normal start
        # path is allowed to recover the persistent cluster.
        status = _run(
            [
                str(pg_ctl),
                "-D",
                str(data_root),
                "status",
            ],
            check=False,
            timeout=10,
        )

        if status.returncode == 3:
            try:
                pid_path.unlink()
            except OSError as exc:
                raise PrivatePostgreSQLError(
                    "Private PostgreSQL is stopped but its stale "
                    "postmaster PID file could not be removed."
                ) from exc
        else:
            raise PrivatePostgreSQLError(
                "Private PostgreSQL has a postmaster PID file but is not "
                "reachable on its persisted port. Manual recovery is required."
            )

    if not pid_path.is_file():
        log_file = paths.logs_dir(create=True) / "private-postgres.log"

        pgctl_env = os.environ.copy()
        pgctl_env["PGUSER"] = cluster_user

        _run(
            [
                str(pg_ctl),
                "-D",
                str(data_root),
                "-l",
                str(log_file),
                "-o",
                f"-p {selected_port} -h {host}",
                "-w",
                "-t",
                str(int(timeout)),
                "start",
            ],
            timeout=timeout + 10,
            capture=False,
            env=pgctl_env,
        )
    _wait_for_server(host, selected_port, timeout=timeout)
    security_state_present = (data_root.parent / "security.json").is_file()
    if not security_state_present:
        _ensure_role_and_database(
            host=host,
            port=selected_port,
            database=database,
            user=cluster_user,
        )
    state = {
        "host": host,
        "port": selected_port,
        "database": database,
        "user": cluster_user,
        "version": runtime_version,
        "data_root": str(data_root),
    }

    if existing_state:
        state["created_at"] = existing_state.get("created_at")
    else:
        state["created_at"] = time.time()
    _write_state(state)
    return PrivatePostgreSQLConfig(
        runtime_root=runtime_root(),
        data_root=data_root,
        host=host,
        port=selected_port,
        database=database,
        user=cluster_user,
        bundled_version=runtime_version,
    )


def stop(
    config: PrivatePostgreSQLConfig,
    *,
    timeout: float = 30.0,
) -> None:
    """Stop only the private PostgreSQL cluster owned by DairyOS."""
    data_root = config.data_root

    if not _pid_file(data_root).is_file():
        return

    _run(
        [
            str(_binary("pg_ctl.exe")),
            "-D",
            str(data_root),
            "stop",
            "-m",
            "fast",
            "-w",
            "-t",
            str(int(timeout)),
        ],
        timeout=timeout + 10,
    )


def status(config: PrivatePostgreSQLConfig) -> PrivatePostgreSQLStatus:
    version = detect_installed_version()
    running = (
        _pid_file(config.data_root).is_file()
        and _is_port_open(config.host, config.port)
    )

    return PrivatePostgreSQLStatus(
        installed=version is not None,
        running=running,
        version=version,
        data_root=config.data_root,
        port=config.port,
    )


def connection_environment(
    config: PrivatePostgreSQLConfig,
) -> dict[str, str]:
    return {
        "DAIRYOS_DB_HOST": config.host,
        "DAIRYOS_DB_PORT": str(config.port),
        "DAIRYOS_DB_NAME": config.database,
        "DAIRYOS_DB_USER": config.user,
        "DAIRYOS_DB_PASSWORD": "",
    }
