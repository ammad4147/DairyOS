"""Database runtime selection for the DairyOS Windows appliance."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dairyos.windows.private_postgres import (
    PrivatePostgreSQLConfig,
    PrivatePostgreSQLError,
    start as start_private_postgres,
)
from dairyos.windows.postgres_service import (
    PostgreSQLServiceError,
    ensure_postgresql_running,
)


class ApplianceDatabaseError(RuntimeError):
    """Raised when DairyOS cannot prepare its database runtime."""


@dataclass(frozen=True)
class ApplianceDatabase:
    """Resolved database runtime used by the application."""

    mode: str
    host: str
    port: int
    database: str
    user: str
    private_postgres: PrivatePostgreSQLConfig | None = None

    @property
    def password(self) -> str:
        """Local appliance database uses passwordless loopback authentication."""
        return ""


def _is_frozen() -> bool:
    return bool(getattr(__import__("sys"), "frozen", False))


def prepare_database(*, postgres_timeout: float = 30.0) -> ApplianceDatabase:
    """Prepare the correct PostgreSQL runtime for the current deployment."""

    if not _is_frozen():
        try:
            ensure_postgresql_running(timeout=postgres_timeout)
        except PostgreSQLServiceError as exc:
            raise ApplianceDatabaseError(
                f"System PostgreSQL could not be prepared: {exc}"
            ) from exc

        host = os.environ.get("DAIRYOS_DB_HOST", "127.0.0.1")
        port = int(os.environ.get("DAIRYOS_DB_PORT", "5432"))
        database = os.environ.get("DAIRYOS_DB_NAME", "dairyos")
        user = os.environ.get("DAIRYOS_DB_USER", "dairyos")

        return ApplianceDatabase(
            mode="system",
            host=host,
            port=port,
            database=database,
            user=user,
        )

    try:
        private = start_private_postgres(timeout=postgres_timeout)
    except (PrivatePostgreSQLError, ValueError) as exc:
        raise ApplianceDatabaseError(
            f"Private DairyOS PostgreSQL could not be prepared: {exc}"
        ) from exc

    return ApplianceDatabase(
        mode="private",
        host=private.host,
        port=private.port,
        database=private.database,
        user=private.user,
        private_postgres=private,
    )


def apply_database_environment(database: ApplianceDatabase) -> None:
    """Make the resolved database authoritative for downstream DairyOS code."""
    os.environ["DAIRYOS_DB_HOST"] = database.host
    os.environ["DAIRYOS_DB_PORT"] = str(database.port)
    os.environ["DAIRYOS_DB_NAME"] = database.database
    os.environ["DAIRYOS_DB_USER"] = database.user
    os.environ["DAIRYOS_DB_PASSWORD"] = ""

    os.environ.pop("DAIRYOS_DATABASE_URL", None)