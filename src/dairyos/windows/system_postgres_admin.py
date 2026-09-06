"""DPAPI-protected dairyos_admin credential adoption for system PostgreSQL."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote

import psycopg

from dairyos.platform import paths
from dairyos.windows.private_database_security import _atomic_json, _protect, _unprotect

CREDENTIAL_VERSION = 1
CREDENTIAL_FILENAME = "system-postgres-admin.json"
ADMIN_ROLE = "dairyos_admin"
MIGRATION_DATABASE_URL_ENV = "DAIRYOS_MIGRATION_DATABASE_URL"


class SystemPostgresAdminCredentialError(RuntimeError):
    """Raised when the system PostgreSQL admin credential cannot be used safely."""


def credential_state_path() -> Path:
    return paths.data_root(create=True) / "security" / CREDENTIAL_FILENAME


def credential_state_exists() -> bool:
    return credential_state_path().is_file()


def _settings() -> tuple[str, int, str]:
    host = os.environ.get("DAIRYOS_DB_HOST", "127.0.0.1")
    try:
        port = int(os.environ.get("DAIRYOS_DB_PORT", "5432"))
    except ValueError as exc:
        raise SystemPostgresAdminCredentialError("DAIRYOS_DB_PORT must be an integer.") from exc
    database = os.environ.get("DAIRYOS_DB_NAME", "dairyos")
    return host, port, database


def _admin_url(password: str, *, host: str, port: int, database: str) -> str:
    return (
        "postgresql+psycopg://"
        f"{quote(ADMIN_ROLE, safe='')}:{quote(password, safe='')}@"
        f"{host}:{port}/{quote(database, safe='')}"
    )


def validate_admin_password(
    password: str,
    *,
    host: str | None = None,
    port: int | None = None,
    database: str | None = None,
) -> None:
    """Validate dairyos_admin by authenticating before any credential is persisted."""
    if not password:
        raise SystemPostgresAdminCredentialError("The dairyos_admin password cannot be empty.")

    default_host, default_port, default_database = _settings()
    resolved_host = host or default_host
    resolved_port = port if port is not None else default_port
    resolved_database = database or default_database

    try:
        with psycopg.connect(
            host=resolved_host,
            port=resolved_port,
            dbname=resolved_database,
            user=ADMIN_ROLE,
            password=password,
            connect_timeout=10,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
    except Exception as exc:
        raise SystemPostgresAdminCredentialError(
            "The dairyos_admin credential could not be validated against system PostgreSQL."
        ) from exc


def adopt_admin_password(password: str) -> Path:
    """Validate, DPAPI-protect, and atomically persist the system admin password."""
    host, port, database = _settings()
    validate_admin_password(password, host=host, port=port, database=database)

    path = credential_state_path()
    _atomic_json(
        path,
        {
            "version": CREDENTIAL_VERSION,
            "role": ADMIN_ROLE,
            "host": host,
            "port": port,
            "database": database,
            "password": _protect(password),
        },
    )
    return path


def _read_password() -> tuple[str, str, int, str]:
    path = credential_state_path()
    if not path.is_file():
        raise SystemPostgresAdminCredentialError(
            "The system PostgreSQL dairyos_admin credential has not been adopted."
        )

    try:
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise TypeError("credential state is not an object")
        if payload.get("version") != CREDENTIAL_VERSION:
            raise ValueError("unsupported credential version")
        if payload.get("role") != ADMIN_ROLE:
            raise ValueError("unexpected database role")

        host = str(payload["host"])
        port = int(payload["port"])
        database = str(payload["database"])
        password = _unprotect(dict(payload["password"]))
    except SystemPostgresAdminCredentialError:
        raise
    except Exception as exc:
        raise SystemPostgresAdminCredentialError(
            "The stored dairyos_admin credential is unreadable and must be repaired."
        ) from exc

    current_host, current_port, current_database = _settings()
    if (host, port, database) != (current_host, current_port, current_database):
        raise SystemPostgresAdminCredentialError(
            "The stored dairyos_admin credential targets a different system PostgreSQL instance and must be repaired."
        )

    return password, host, port, database


def migration_database_url() -> str:
    password, host, port, database = _read_password()
    return _admin_url(password, host=host, port=port, database=database)


def stage_migration_database_url() -> None:
    """Stage the privileged URL only when another authority has not already done so."""
    if os.environ.get(MIGRATION_DATABASE_URL_ENV, "").strip():
        return
    os.environ[MIGRATION_DATABASE_URL_ENV] = migration_database_url()
