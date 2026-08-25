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
import time
from urllib.error import URLError
from urllib.request import urlopen

from dairyos.windows.migrations import MigrationGateError, migrate_if_needed
from dairyos.windows.postgres_service import PostgreSQLServiceError, ensure_postgresql_running

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
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        if not kernel32.AssignProcessToJobObject(self.handle, wintypes.HANDLE(process._handle)):
            raise ctypes.WinError(ctypes.get_last_error())

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
    """Resolve the frozen backend executable, with a development fallback."""
    configured = os.environ.get("DAIRYOS_BACKEND_EXE")
    if configured:
        return [configured, "--host", host, "--port", str(port)]

    sibling = Path(sys.executable).with_name("DairyOS-Server.exe")
    if os.name == "nt" and sibling.is_file():
        return [str(sibling), "--host", host, "--port", str(port)]

    return [sys.executable, "-m", "dairyos.server", "--host", host, "--port", str(port)]


def start_backend(config: SupervisorConfig, job: JobObject) -> tuple[subprocess.Popen, str]:
    port = config.port or choose_port(config.host)
    command = backend_command(config.host, port)
    env = os.environ.copy()
    env["DAIRYOS_HOST"] = config.host
    env["DAIRYOS_PORT"] = str(port)
    LOG.info("Starting DairyOS backend on %s:%s", config.host, port)
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    process = subprocess.Popen(command, env=env, creationflags=creationflags)
    job.assign(process)
    return process, f"http://{config.host}:{port}"


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


def show_startup_error(title: str, message: str) -> None:
    if os.name == "nt":
        ctypes.windll.user32.MessageBoxW(None, message, title, 0x10)
    else:
        LOG.error("%s: %s", title, message)


def launch_webview(url: str, on_closed) -> None:
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
    window.events.closed += lambda: on_closed()
    webview.start(gui="edgechromium", debug=False)


def run(config: SupervisorConfig) -> int:
    instance = SingleInstance()
    if not instance.acquire():
        LOG.warning("Another DairyOS instance is already running")
        return 2

    job = JobObject()
    backend = None
    try:
        try:
            service_name = ensure_postgresql_running(timeout=config.postgres_timeout)
            if service_name != "non-windows":
                LOG.info("PostgreSQL Windows Service is running: %s", service_name)
        except PostgreSQLServiceError as exc:
            LOG.exception("DairyOS PostgreSQL service preflight failed")
            show_startup_error(
                "DairyOS database service unavailable",
                "DairyOS could not start PostgreSQL.\n\n"
                f"{exc}\n\n"
                "No application window was started. Farm data was not modified.",
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

        job.create()
        attempts = config.restart_attempts + 1
        for attempt in range(attempts):
            try:
                backend, url = start_backend(config, job)
                wait_for_ready(url, config)
                LOG.info("DairyOS backend ready at %s", url)
                launch_webview(url, lambda: terminate_backend(backend))
                return 0
            except Exception as exc:
                LOG.exception("DairyOS desktop startup/runtime failure")
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
        terminate_backend(backend)
        job.close()
        instance.release()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dairyos-desktop")
    parser.add_argument("--host", default=os.environ.get("DAIRYOS_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("DAIRYOS_PORT", "0")))
    parser.add_argument("--health-timeout", type=float, default=60.0)
    parser.add_argument("--restart-attempts", type=int, default=2)
    parser.add_argument("--postgres-timeout", type=float, default=30.0)
    parser.add_argument("--log-level", default=os.environ.get("DAIRYOS_LOG_LEVEL", "INFO"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    if os.name != "nt":
        LOG.warning("Desktop supervisor is running on a non-Windows host; Job Object and WebView2 are unavailable.")
    return run(
        SupervisorConfig(
            host=args.host,
            port=args.port,
            health_timeout=args.health_timeout,
            restart_attempts=max(0, args.restart_attempts),
            postgres_timeout=max(1.0, args.postgres_timeout),
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
