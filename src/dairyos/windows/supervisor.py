"""Windows desktop supervisor for the DairyOS local web runtime.

The supervisor owns only the application lifecycle. PostgreSQL is an
independent Windows Service and is never made a child process of DairyOS.
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import logging
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
from urllib.error import URLError
from urllib.request import urlopen

from dairyos.windows.appliance_database import (
    ApplianceDatabaseError,
    apply_database_environment,
    prepare_database,
)
from dairyos.windows.migrations import MigrationGateError, migrate_if_needed
from dairyos.windows.private_postgres import stop as stop_private_postgres
from dairyos.windows.postgres_service import PostgreSQLServiceError, ensure_postgresql_running
from dairyos.windows.system_postgres_admin import (
    SystemPostgresAdminCredentialError,
    SystemPostgresRuntimeCredentialError,
    stage_migration_database_url,
    stage_runtime_database_url,
)

LOG = logging.getLogger("dairyos.windows.supervisor")


@dataclass(frozen=True)
class SupervisorConfig:
    host: str = "127.0.0.1"
    port: int = 0
    health_timeout: float = 60.0
    health_interval: float = 0.5
    restart_attempts: int = 2
    restart_backoff: float = 1.5
    postgres_timeout: float = 30.0


class SingleInstance:
    """Windows named mutex; a no-op on non-Windows development hosts."""

    ERROR_ALREADY_EXISTS = 183

    def __init__(self, name: str = "Global\\DairyOS.Desktop.SingleInstance"):
        self.name = name
        self.handle = None

    def acquire(self) -> bool:
        if os.name != "nt":
            return True
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        ctypes.set_last_error(0)
        self.handle = kernel32.CreateMutexW(None, False, self.name)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        if ctypes.get_last_error() == self.ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(self.handle)
            self.handle = None
            return False
        return True

    def release(self) -> None:
        if self.handle and os.name == "nt":
            ctypes.WinDLL("kernel32", use_last_error=True).CloseHandle(self.handle)
            self.handle = None


class _IOCounters(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class _BasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _ExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BasicLimitInformation),
        ("IoInfo", _IOCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class JobObject:
    """Contain the backend so it cannot survive a dead supervisor."""

    JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000

    def __init__(self):
        self.handle = None

    def create(self) -> None:
        if os.name != "nt":
            return
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        self.handle = kernel32.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = _ExtendedLimitInformation()
        limits.BasicLimitInformation.LimitFlags = self.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            wintypes.INT,
            wintypes.LPVOID,
            wintypes.DWORD,
        ]
        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        if not kernel32.SetInformationJobObject(
            self.handle,
            self.JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limits),
            ctypes.sizeof(limits),
        ):
            raise ctypes.WinError(ctypes.get_last_error())

    def assign(self, process: subprocess.Popen) -> None:
        if os.name != "nt" or not self.handle:
            return

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.AssignProcessToJobObject.argtypes = [
            wintypes.HANDLE,
            wintypes.HANDLE,
        ]
        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL

        if not kernel32.AssignProcessToJobObject(
            self.handle,
            wintypes.HANDLE(process._handle),
        ):
            raise ctypes.WinError(ctypes.get_last_error())

    def assign_pid(self, pid: int) -> None:
        """Assign an already-running Windows process to this Job Object."""
        if os.name != "nt" or not self.handle:
            return

        if pid <= 0:
            raise ValueError("pid must be positive")

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        PROCESS_TERMINATE = 0x0001
        PROCESS_SET_QUOTA = 0x0100

        kernel32.OpenProcess.argtypes = [
            wintypes.DWORD,
            wintypes.BOOL,
            wintypes.DWORD,
        ]
        kernel32.OpenProcess.restype = wintypes.HANDLE

        kernel32.AssignProcessToJobObject.argtypes = [
            wintypes.HANDLE,
            wintypes.HANDLE,
        ]
        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL

        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        process_handle = kernel32.OpenProcess(
            PROCESS_TERMINATE | PROCESS_SET_QUOTA,
            False,
            pid,
        )

        if not process_handle:
            raise ctypes.WinError(ctypes.get_last_error())

        try:
            if not kernel32.AssignProcessToJobObject(
                self.handle,
                process_handle,
            ):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            kernel32.CloseHandle(process_handle)

    def close(self) -> None:
        if self.handle and os.name == "nt":
            ctypes.WinDLL("kernel32", use_last_error=True).CloseHandle(self.handle)
            self.handle = None


def choose_port(host: str = "127.0.0.1") -> int:
    """Choose an ephemeral loopback port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def probe(url: str, timeout: float = 1.0) -> bool:
    try:
        with urlopen(url, timeout=timeout) as response:
            return 200 <= response.status < 300
    except (OSError, URLError):
        return False


def wait_for_ready(base_url: str, config: SupervisorConfig) -> None:
    deadline = time.monotonic() + config.health_timeout
    health_url = f"{base_url}/health"
    readiness_url = f"{base_url}/readiness"
    health_seen = False
    while time.monotonic() < deadline:
        if probe(health_url):
            health_seen = True
            if probe(readiness_url):
                return
        time.sleep(config.health_interval)
    if not health_seen:
        raise RuntimeError("DairyOS backend did not become healthy before the startup timeout.")
    raise RuntimeError("DairyOS backend is healthy but did not become ready before the startup timeout.")


def backend_command(host: str, port: int) -> list[str]:
    """Resolve the backend command.

    Frozen Windows builds use a single DairyOS.exe. The same executable is
    launched in hidden backend mode. Development runs use the normal Python
    module entry point.
    """
    if getattr(sys, "frozen", False):
        return [
            sys.executable,
            "--dairyos-backend",
            "--host",
            host,
            "--port",
            str(port),
        ]

    configured = os.environ.get("DAIRYOS_BACKEND_EXE")
    if configured:
        return [configured, "--host", host, "--port", str(port)]

    return [
        sys.executable,
        "-m",
        "dairyos.server",
        "--host",
        host,
        "--port",
        str(port),
    ]


def start_backend(config: SupervisorConfig, job: JobObject, port: int | None = None) -> tuple[subprocess.Popen, str]:
    selected_port = port or config.port or choose_port(config.host)
    command = backend_command(config.host, selected_port)
    env = os.environ.copy()
    env["DAIRYOS_HOST"] = config.host
    env["DAIRYOS_PORT"] = str(selected_port)
    # Privileged database access is migration-only and must never reach the
    # restricted backend child, even if an upstream cleanup regresses.
    env.pop("DAIRYOS_MIGRATION_DATABASE_URL", None)
    LOG.info("Starting DairyOS backend on %s:%s", config.host, selected_port)

    # The frozen desktop build is windowed, so the backend child has no
    # visible console. Persist stdout/stderr so a frozen-startup failure
    # can be diagnosed without changing application behavior.
    runtime_log_dir = Path(os.environ.get("DAIRYOS_RUNTIME_LOG_DIR", os.environ.get("TEMP", ".")))
    runtime_log_dir.mkdir(parents=True, exist_ok=True)
    backend_log_path = runtime_log_dir / "dairyos-backend.log"
    backend_log = open(backend_log_path, "ab", buffering=0)

    env["DAIRYOS_BACKEND_LOG"] = str(backend_log_path)

    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    process = subprocess.Popen(
        command,
        env=env,
        creationflags=creationflags,
        stdout=backend_log,
        stderr=backend_log,
    )
    job.assign(process)

    LOG.info("DairyOS backend child log: %s", backend_log_path)
    return process, f"http://{config.host}:{selected_port}"


def terminate_backend(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    LOG.info("Stopping DairyOS backend")
    try:
        process.terminate()
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        LOG.warning("Backend did not stop within the graceful shutdown window; killing it")
        process.kill()
        process.wait(timeout=5)


class BackendWatchdog:
    """Monitor the backend while WebView2 is open and recover bounded crashes."""

    def __init__(self, process, url: str, config: SupervisorConfig, job: JobObject, on_restart):
        self.process = process
        self.url = url
        self.config = config
        self.job = job
        self.on_restart = on_restart
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.failure: Exception | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        self.thread = threading.Thread(target=self._watch, name="dairyos-backend-watchdog", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread is not None and self.thread is not threading.current_thread():
            self.thread.join(timeout=5)

    def _watch(self) -> None:
        attempts = 0
        while not self.stop_event.wait(0.25):
            if self.process.poll() is None:
                continue

            attempts += 1
            if attempts > self.config.restart_attempts:
                self.failure = RuntimeError("DairyOS backend exceeded the automatic restart limit.")
                LOG.error("DairyOS backend crash-loop limit reached")
                return

            delay = self.config.restart_backoff * attempts
            LOG.warning("DairyOS backend exited; restarting attempt %s/%s after %.1fs", attempts, self.config.restart_attempts, delay)
            if self.stop_event.wait(delay):
                return

            try:
                with self._lock:
                    new_process, new_url = start_backend(self.config, self.job, port=_url_port(self.url))
                    wait_for_ready(new_url, self.config)
                    old_process = self.process
                    self.process = new_process
                    self.url = new_url
                terminate_backend(old_process)
                attempts = 0
                self.failure = None
                self.on_restart(new_url)
                LOG.info("DairyOS backend recovered at %s", new_url)
            except Exception as exc:
                LOG.exception("DairyOS backend restart attempt failed")
                self.failure = exc
                terminate_backend(locals().get("new_process"))
                if attempts >= self.config.restart_attempts:
                    return


def _url_port(url: str) -> int:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.port is None:
        raise RuntimeError(f"DairyOS backend URL has no explicit port: {url}")
    return parsed.port


def show_startup_error(title: str, message: str) -> None:
    if os.name == "nt":
        ctypes.windll.user32.MessageBoxW(None, message, title, 0x10)
    else:
        LOG.error("%s: %s", title, message)


def launch_webview(url: str, watchdog: BackendWatchdog, on_closed) -> None:
    try:
        import webview
    except ImportError as exc:
        raise RuntimeError("pywebview is required for the packaged DairyOS desktop shell.") from exc

    window = webview.create_window(
        "DairyOS",
        url,
        width=1440,
        height=900,
        min_size=(1024, 700),
        text_select=True,
    )

    def reload_url(new_url: str) -> None:
        try:
            window.load_url(new_url)
        except Exception:
            LOG.exception("Failed to reload the DairyOS WebView after backend recovery")

    watchdog.on_restart = reload_url

    def close_application() -> None:
        # Signal the watchdog first so an intentional backend termination
        # cannot be classified as a crash/restart-limit failure.
        watchdog.stop()
        on_closed()

    window.events.closed += close_application
    watchdog.start()
    try:
        webview.start(gui="edgechromium", debug=False)
    finally:
        watchdog.stop()


def database_preflight(config: SupervisorConfig) -> int:
    """Exercise the packaged database startup path without opening the UI."""
    private_database = None
    try:
        database = prepare_database(
            postgres_timeout=config.postgres_timeout
        )
        private_database = database.private_postgres
        if private_database is None:
            raise ApplianceDatabaseError(
                "Packaged database preflight did not resolve private PostgreSQL."
            )

        apply_database_environment(database)
        migration = migrate_if_needed()
        LOG.info(
            "Installed database preflight passed: migrated=%s current=%s "
            "target=%s backup=%s",
            migration.migrated,
            migration.current_heads,
            migration.target_heads,
            migration.backup_path,
        )
        return 0
    except (ApplianceDatabaseError, MigrationGateError) as exc:
        LOG.exception("Installed DairyOS database preflight failed")
        return 4
    finally:
        if private_database is not None:
            try:
                stop_private_postgres(private_database)
            except Exception:
                LOG.exception(
                    "Failed to stop private PostgreSQL after database preflight"
                )


def run(config: SupervisorConfig) -> int:
    instance = SingleInstance()
    if not instance.acquire():
        LOG.warning("Another DairyOS instance is already running")
        return 2

    job = JobObject()
    backend = None
    watchdog = None
    private_database = None
    try:
        job.create()

        try:
            if getattr(sys, "frozen", False):
                database = prepare_database(
                    postgres_timeout=config.postgres_timeout
                )
                private_database = database.private_postgres

                if private_database is not None and os.name == "nt":
                    pid_file = private_database.data_root / "postmaster.pid"

                    if not pid_file.is_file():
                        raise ApplianceDatabaseError(
                            "Private PostgreSQL started without a postmaster PID file."
                        )

                    pid_text = pid_file.read_text(
                        encoding="utf-8",
                        errors="replace",
                    ).splitlines()

                    if not pid_text or not pid_text[0].strip().isdigit():
                        raise ApplianceDatabaseError(
                            "Private PostgreSQL postmaster PID file is invalid."
                        )

                    private_pid = int(pid_text[0].strip())
                    job.assign_pid(private_pid)

                    LOG.info(
                        "Private PostgreSQL PID %s assigned to DairyOS Job Object",
                        private_pid,
                    )

                apply_database_environment(database)

                LOG.info(
                    "DairyOS packaged database ready: mode=%s host=%s port=%s",
                    database.mode,
                    database.host,
                    database.port,
                )
            else:
                service_name = ensure_postgresql_running(
                    timeout=config.postgres_timeout
                )
                if service_name != "non-windows":
                    LOG.info(
                        "PostgreSQL Windows Service is running: %s",
                        service_name,
                    )
                stage_runtime_database_url()
                stage_migration_database_url()
        except (
            PostgreSQLServiceError,
            ApplianceDatabaseError,
            SystemPostgresAdminCredentialError,
            SystemPostgresRuntimeCredentialError,
        ) as exc:
            LOG.exception("DairyOS database runtime preflight failed")
            show_startup_error(
                "DairyOS database unavailable",
                "DairyOS could not prepare its database runtime.\n\n"
                f"{exc}\n\n"
                "No application window was started. Existing farm data was not intentionally deleted.",
            )
            return 4

        try:
            migration = migrate_if_needed()
            LOG.info(
                "Database migration gate passed: migrated=%s current=%s target=%s backup=%s",
                migration.migrated,
                migration.current_heads,
                migration.target_heads,
                migration.backup_path,
            )
        except MigrationGateError as exc:
            LOG.exception("DairyOS database startup gate failed")
            show_startup_error(
                "DairyOS database startup blocked",
                "DairyOS could not safely prepare the farm database.\n\n"
                f"{exc}\n\n"
                "No application window was started. Existing farm data was not intentionally deleted.",
            )
            return 3

        attempts = config.restart_attempts + 1
        for attempt in range(attempts):
            try:
                backend, url = start_backend(config, job)
                wait_for_ready(url, config)
                LOG.info("DairyOS backend ready at %s", url)
                watchdog = BackendWatchdog(backend, url, config, job, lambda _url: None)
                launch_webview(url, watchdog, lambda: terminate_backend(watchdog.process))
                return 0 if watchdog.failure is None else 1
            except Exception as exc:
                LOG.exception("DairyOS desktop startup/runtime failure")
                if watchdog is not None:
                    watchdog.stop()
                terminate_backend(backend)
                backend = None
                if attempt + 1 >= attempts:
                    show_startup_error(
                        "DairyOS could not start",
                        "The DairyOS application runtime failed to start or become ready.\n\n"
                        f"{exc}\n\nReview the DairyOS logs for diagnostic details.",
                    )
                    return 1
                time.sleep(config.restart_backoff * (attempt + 1))
        return 1
    finally:
        if watchdog is not None:
            watchdog.stop()
        terminate_backend(watchdog.process if watchdog is not None else backend)

        if private_database is not None:
            try:
                stop_private_postgres(private_database)
            except Exception:
                LOG.exception(
                    "Failed to stop private DairyOS PostgreSQL cleanly"
                )

        job.close()
        instance.release()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dairyos-desktop")
    parser.add_argument("--host", default=os.environ.get("DAIRYOS_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("DAIRYOS_PORT", "0")))
    parser.add_argument("--health-timeout", type=float, default=60.0)
    parser.add_argument("--restart-attempts", type=int, default=2)
    parser.add_argument("--postgres-timeout", type=float, default=30.0)
    parser.add_argument("--database-preflight", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--log-level", default=os.environ.get("DAIRYOS_LOG_LEVEL", "INFO"))
    return parser


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if "--dairyos-backend" in argv:
        backend_argv = [arg for arg in argv if arg != "--dairyos-backend"]
        from dairyos.server import main as server_main

        return server_main(backend_argv)

    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    if os.name != "nt":
        LOG.warning("Desktop supervisor is running on a non-Windows host; Job Object and WebView2 are unavailable.")

    config = SupervisorConfig(
        host=args.host,
        port=args.port,
        health_timeout=args.health_timeout,
        restart_attempts=max(0, args.restart_attempts),
        postgres_timeout=max(1.0, args.postgres_timeout),
    )
    if args.database_preflight:
        if not getattr(sys, "frozen", False):
            LOG.error("--database-preflight is reserved for the packaged DairyOS executable.")
            return 64
        return database_preflight(config)
    return run(config)


if __name__ == "__main__":
    raise SystemExit(main())
