"""DPAPI-protected PostgreSQL credentials for DairyOS system deployments.\n\nThe privileged dairyos_admin credential is migration-only. The restricted\ndairyos credential is used by the application runtime only when system\nPostgreSQL requires password authentication. Genuine passwordless loopback\ndeployments remain supported without storing a runtime password.\n"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote

import psycopg

from dairyos.platform import paths
from dairyos.windows.private_database_security import _atomic_json, _protect, _unprotect

CREDENTIAL_VERSION = 1
CREDENTIAL_FILENAME = "system-postgres-admin.json"
RUNTIME_CREDENTIAL_FILENAME = "system-postgres-runtime.json"
ADMIN_ROLE = "dairyos_admin"
APP_ROLE = "dairyos"
MIGRATION_DATABASE_URL_ENV = "DAIRYOS_MIGRATION_DATABASE_URL"
DATABASE_URL_ENV = "DAIRYOS_DATABASE_URL"
DATABASE_PASSWORD_ENV = "DAIRYOS_DB_PASSWORD"
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


class SystemPostgresAdminCredentialError(RuntimeError):
    """Raised when the system PostgreSQL admin credential cannot be used safely."""


class SystemPostgresRuntimeCredentialError(RuntimeError):
    """Raised when restricted system PostgreSQL runtime access is unavailable."""


def credential_state_path() -> Path:
    return paths.data_root(create=True) / "security" / CREDENTIAL_FILENAME


def credential_state_exists() -> bool:
    return credential_state_path().is_file()


def runtime_credential_state_path() -> Path:
    return paths.data_root(create=True) / "security" / RUNTIME_CREDENTIAL_FILENAME


def runtime_credential_state_exists() -> bool:
    return runtime_credential_state_path().is_file()


def _settings() -> tuple[str, int, str]:
    host = os.environ.get("DAIRYOS_DB_HOST", "127.0.0.1")
    try:
        port = int(os.environ.get("DAIRYOS_DB_PORT", "5432"))
    except ValueError as exc:
        raise SystemPostgresAdminCredentialError("DAIRYOS_DB_PORT must be an integer.") from exc
    database = os.environ.get("DAIRYOS_DB_NAME", "dairyos")
    return host, port, database


def _role_url(
    role: str,
    password: str,
    *,
    host: str,
    port: int,
    database: str,
) -> str:
    return (
        "postgresql+psycopg://"
        f"{quote(role, safe='')}:{quote(password, safe='')}@"
        f"{host}:{port}/{quote(database, safe='')}"
    )


def _admin_url(password: str, *, host: str, port: int, database: str) -> str:
    return _role_url(
        ADMIN_ROLE,
        password,
        host=host,
        port=port,
        database=database,
    )


def _runtime_url(password: str, *, host: str, port: int, database: str) -> str:
    return _role_url(
        APP_ROLE,
        password,
        host=host,
        port=port,
        database=database,
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


def validate_stored_admin_credential() -> None:
    """Decrypt and authenticate the adopted credential without changing storage."""
    password, host, port, database = _read_password()
    validate_admin_password(password, host=host, port=port, database=database)


def migration_database_url() -> str:
    password, host, port, database = _read_password()
    return _admin_url(password, host=host, port=port, database=database)


def stage_migration_database_url() -> None:
    """Stage the privileged URL only when another authority has not already done so."""
    if os.environ.get(MIGRATION_DATABASE_URL_ENV, "").strip():
        return
    os.environ[MIGRATION_DATABASE_URL_ENV] = migration_database_url()


def _connect_runtime(
    *,
    password: str | None,
    host: str,
    port: int,
    database: str,
) -> None:
    try:
        with psycopg.connect(
            host=host,
            port=port,
            dbname=database,
            user=APP_ROLE,
            password=password,
            connect_timeout=10,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
    except Exception as exc:
        raise SystemPostgresRuntimeCredentialError(
            "The restricted dairyos database credential could not authenticate "
            "against system PostgreSQL."
        ) from exc


def passwordless_runtime_available() -> bool:
    """Return whether governed loopback access works without a password."""
    host, port, database = _settings()
    if host not in LOOPBACK_HOSTS or database != "dairyos":
        return False
    try:
        _connect_runtime(
            password=None,
            host=host,
            port=port,
            database=database,
        )
    except SystemPostgresRuntimeCredentialError:
        return False
    return True


def validate_runtime_password(
    password: str,
    *,
    host: str | None = None,
    port: int | None = None,
    database: str | None = None,
) -> None:
    """Authenticate the restricted dairyos role before persisting its password."""
    if not password:
        raise SystemPostgresRuntimeCredentialError(
            "The dairyos runtime password cannot be empty."
        )

    default_host, default_port, default_database = _settings()
    _connect_runtime(
        password=password,
        host=host or default_host,
        port=port if port is not None else default_port,
        database=database or default_database,
    )


def adopt_runtime_password(password: str) -> Path:
    """Validate and DPAPI-protect the restricted system PostgreSQL credential."""
    host, port, database = _settings()
    validate_runtime_password(
        password,
        host=host,
        port=port,
        database=database,
    )
    path = runtime_credential_state_path()
    _atomic_json(
        path,
        {
            "version": CREDENTIAL_VERSION,
            "role": APP_ROLE,
            "host": host,
            "port": port,
            "database": database,
            "password": _protect(password),
        },
    )
    return path


def _read_runtime_password() -> tuple[str, str, int, str]:
    path = runtime_credential_state_path()
    if not path.is_file():
        raise SystemPostgresRuntimeCredentialError(
            "The system PostgreSQL dairyos runtime credential has not been adopted."
        )

    try:
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise TypeError("credential state is not an object")
        if payload.get("version") != CREDENTIAL_VERSION:
            raise ValueError("unsupported credential version")
        if payload.get("role") != APP_ROLE:
            raise ValueError("unexpected database role")

        host = str(payload["host"])
        port = int(payload["port"])
        database = str(payload["database"])
        password = _unprotect(dict(payload["password"]))
    except Exception as exc:
        raise SystemPostgresRuntimeCredentialError(
            "The stored dairyos runtime credential is unreadable and must be repaired."
        ) from exc

    current_host, current_port, current_database = _settings()
    if (host, port, database) != (
        current_host,
        current_port,
        current_database,
    ):
        raise SystemPostgresRuntimeCredentialError(
            "The stored dairyos runtime credential targets a different system "
            "PostgreSQL instance and must be repaired."
        )

    return password, host, port, database


def validate_stored_runtime_credential() -> None:
    password, host, port, database = _read_runtime_password()
    validate_runtime_password(
        password,
        host=host,
        port=port,
        database=database,
    )


def runtime_database_url() -> str:
    password, host, port, database = _read_runtime_password()
    return _runtime_url(
        password,
        host=host,
        port=port,
        database=database,
    )


def validate_runtime_database_access() -> str:
    """Validate the configured runtime path without altering process state."""
    if runtime_credential_state_exists():
        validate_stored_runtime_credential()
        return "protected"

    if passwordless_runtime_available():
        return "passwordless"

    if os.environ.get(DATABASE_URL_ENV, "").strip() or os.environ.get(
        DATABASE_PASSWORD_ENV, ""
    ).strip():
        return "environment-override"

    raise SystemPostgresRuntimeCredentialError(
        "System PostgreSQL requires a restricted dairyos runtime credential. "
        "Adopt it once so normal DairyOS startup does not depend on a manually "
        "maintained database password environment variable."
    )


def stage_runtime_database_url() -> None:
    """Stage restricted runtime access for the backend when password auth is required."""
    if os.environ.get(DATABASE_URL_ENV, "").strip() or os.environ.get(
        DATABASE_PASSWORD_ENV, ""
    ).strip():
        return

    if runtime_credential_state_exists():
        validate_stored_runtime_credential()
        os.environ[DATABASE_URL_ENV] = runtime_database_url()
        return

    if passwordless_runtime_available():
        return

    raise SystemPostgresRuntimeCredentialError(
        "System PostgreSQL requires password authentication for the dairyos role, "
        "but no protected runtime credential is available."
    )

