"""Database runtime selection for the DairyOS Windows appliance."""

from __future__ import annotations

from dataclasses import dataclass
import os

from dairyos.windows import private_postgres
from dairyos.windows.private_database_security import (
    application_password,
    application_role,
    admin_database_url,
    backup_database_url,
    ensure_private_database_security,
    install_steady_state_hba_before_start_if_available,
)
from dairyos.windows.private_postgres import (
    PrivatePostgreSQLConfig,
    PrivatePostgreSQLError,
)
from dairyos.windows.postgres_service import (
    PostgreSQLServiceError,
    ensure_postgresql_running,
)


# Preserve the established injection seam used by Windows runtime tests while
# allowing the private_postgres module's HBA writer to be hardened in place.
start_private_postgres = private_postgres.start


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
    password_value: str = ""
    migration_database_url: str | None = None
    backup_database_url: str | None = None
    private_postgres: PrivatePostgreSQLConfig | None = None

    @property
    def password(self) -> str:
        return self.password_value


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
        password = os.environ.get("DAIRYOS_DB_PASSWORD", "")

        return ApplianceDatabase(
            mode="system",
            host=host,
            port=port,
            database=database,
            user=user,
            password_value=password,
        )

    try:
        # Once a private cluster has been hardened, prevent the legacy startup
        # helper from temporarily writing loopback trust rules back into
        # pg_hba.conf on subsequent launches.
        install_steady_state_hba_before_start_if_available()
        private = start_private_postgres(timeout=postgres_timeout)
        ensure_private_database_security(private)
    except Exception as exc:
        # A partial role/security provision must block startup rather than fall
        # through to an unprotected database.
        raise ApplianceDatabaseError(
            f"Private DairyOS PostgreSQL could not be securely prepared: {exc}"
        ) from exc

    return ApplianceDatabase(
        mode="private",
        host=private.host,
        port=private.port,
        database=private.database,
        user=application_role(private),
        password_value=application_password(private),
        migration_database_url=admin_database_url(private),
        backup_database_url=backup_database_url(private),
        private_postgres=private,
    )


def apply_database_environment(database: ApplianceDatabase) -> None:
    """Make the restricted application database identity authoritative.

    A packaged private cluster also supplies a one-use migration URL for the
    startup migration gate. ``migrate_if_needed`` consumes and removes that
    environment variable before the normal backend child is launched.
    """
    os.environ["DAIRYOS_DB_HOST"] = database.host
    os.environ["DAIRYOS_DB_PORT"] = str(database.port)
    os.environ["DAIRYOS_DB_NAME"] = database.database
    os.environ["DAIRYOS_DB_USER"] = database.user
    os.environ["DAIRYOS_DB_PASSWORD"] = database.password

    os.environ.pop("DAIRYOS_DATABASE_URL", None)

    if database.migration_database_url:
        os.environ["DAIRYOS_MIGRATION_DATABASE_URL"] = database.migration_database_url
    else:
        os.environ.pop("DAIRYOS_MIGRATION_DATABASE_URL", None)
