"""Windows Service preflight for the independently managed PostgreSQL service."""

from __future__ import annotations

import os
import re
import subprocess
import time


class PostgreSQLServiceError(RuntimeError):
    """Raised when the local PostgreSQL Windows Service cannot be used."""


_SERVICE_NAME_RE = re.compile(r"^\s*SERVICE_NAME:\s*(\S+)\s*$", re.IGNORECASE)
_PG_VERSION_RE = re.compile(r"postgresql(?:-x64)?-(\d+)$", re.IGNORECASE)
_STATE_RUNNING_RE = re.compile(r"^\s*STATE\s*:\s*4\s+RUNNING\b", re.IGNORECASE)


def _run_sc(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["sc.exe", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _service_sort_key(name: str) -> tuple[int, str]:
    match = _PG_VERSION_RE.search(name)
    version = int(match.group(1)) if match else -1
    return (-version, name.casefold())


def list_postgresql_services() -> list[str]:
    """Return installed PostgreSQL service names in stable newest-first order."""
    if os.name != "nt":
        return []

    result = _run_sc("query", "type=", "service", "state=", "all")
    if result.returncode != 0:
        raise PostgreSQLServiceError(
            f"Unable to enumerate Windows services: {result.stdout.strip()} {result.stderr.strip()}".strip()
        )

    names: list[str] = []
    for line in result.stdout.splitlines():
        match = _SERVICE_NAME_RE.match(line)
        if match and match.group(1).lower().startswith("postgresql"):
            names.append(match.group(1))

    return sorted(names, key=_service_sort_key)


def configured_service_name() -> str | None:
    value = os.environ.get("DAIRYOS_POSTGRES_SERVICE", "").strip()
    return value or None


def resolve_service_name() -> str:
    configured = configured_service_name()
    if configured:
        return configured

    services = list_postgresql_services()
    if not services:
        raise PostgreSQLServiceError(
            "No PostgreSQL Windows Service was found. DairyOS requires PostgreSQL "
            "to be installed before the application can start."
        )
    if len(services) > 1:
        raise PostgreSQLServiceError(
            "Multiple PostgreSQL Windows Services were found and DairyOS cannot "
            "safely choose between them. Set DAIRYOS_POSTGRES_SERVICE explicitly. "
            f"Detected services: {', '.join(services)}"
        )
    return services[0]


def service_is_running(service_name: str) -> bool:
    result = _run_sc("query", service_name)
    if result.returncode != 0:
        return False
    return any(_STATE_RUNNING_RE.match(line) for line in result.stdout.splitlines())


def ensure_postgresql_running(
    *,
    timeout: float = 30.0,
    interval: float = 0.5,
) -> str:
    """Ensure PostgreSQL is running without owning its shutdown lifecycle."""
    if os.name != "nt":
        return "non-windows"

    service_name = resolve_service_name()
    if service_is_running(service_name):
        return service_name

    result = _run_sc("start", service_name)
    if result.returncode != 0 and not service_is_running(service_name):
        details = " ".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
        raise PostgreSQLServiceError(
            f"PostgreSQL service '{service_name}' could not be started. {details}".strip()
        )

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if service_is_running(service_name):
            return service_name
        time.sleep(interval)

    raise PostgreSQLServiceError(
        f"PostgreSQL service '{service_name}' did not reach RUNNING state within {timeout:g} seconds."
    )
