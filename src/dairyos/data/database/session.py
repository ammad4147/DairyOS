import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import sessionmaker

from dairyos.data.database.base import Base

__all__ = ["DATABASE_URL", "Base", "SessionLocal", "engine", "get_session"]

# ------------------------------------------------------------------
# Database connection configuration
# ------------------------------------------------------------------
#
# DairyOS uses the dedicated ``dairyos`` PostgreSQL role for the local
# development/test installation. The local PostgreSQL pg_hba.conf grants
# that role trust authentication on the DairyOS database over loopback,
# so a password is not required for normal local operation.
#
# Deployments may override this through DAIRYOS_DATABASE_URL or the
# explicit DAIRYOS_DB_* environment variables.
# ------------------------------------------------------------------

load_dotenv()


def _validate_explicit_database_url(explicit_url: str, environment: str) -> None:
    """Reject passwordless non-local production URLs without exposing secrets."""
    if environment not in {"production", "staging", "preprod"}:
        return

    try:
        parsed = make_url(explicit_url)
    except ArgumentError as exc:
        raise RuntimeError("DAIRYOS_DATABASE_URL is not a valid database URL.") from exc

    local_loopback = parsed.host in {"localhost", "127.0.0.1", "::1"}
    local_passwordless = (
        not parsed.password
        and parsed.username == "dairyos"
        and local_loopback
        and (parsed.database == "dairyos" or "test" in (parsed.database or "").lower())
    )
    if not parsed.password and not local_passwordless:
        raise RuntimeError(
            "DAIRYOS_DATABASE_URL must include credentials for non-local "
            "production database access."
        )


def _build_database_url() -> str:
    environment = os.getenv("DAIRYOS_ENV", "development").strip().lower()
    explicit_url = os.getenv("DAIRYOS_DATABASE_URL")
    if explicit_url:
        _validate_explicit_database_url(explicit_url, environment)
        return explicit_url

    host = os.getenv("DAIRYOS_DB_HOST", "localhost")
    port = os.getenv("DAIRYOS_DB_PORT", "5432")
    name = os.getenv("DAIRYOS_DB_NAME", "dairyos")
    user = os.getenv("DAIRYOS_DB_USER", "dairyos")
    password = os.getenv("DAIRYOS_DB_PASSWORD")

    local_loopback = user == "dairyos" and host in {"localhost", "127.0.0.1", "::1"}
    # The bundled Windows appliance stages its protected runtime URL before
    # importing this module.  Passwordless local access is also valid for
    # explicitly disposable test databases, so the test suite never needs a
    # secret merely to prove its database isolation guard.
    disposable_test_database = "test" in name.lower()
    local_passwordless = (
        not password
        and local_loopback
        and (name == "dairyos" or disposable_test_database)
    )

    if (
        password is None
        and not local_passwordless
        and environment in {"production", "staging", "preprod"}
    ):
        raise RuntimeError(
            "DAIRYOS_DB_PASSWORD (or DAIRYOS_DATABASE_URL) must be "
            "configured for non-local production database access."
        )

    try:
        port_number = int(port)
    except ValueError as exc:
        raise RuntimeError(f"DAIRYOS_DB_PORT must be an integer, got {port!r}") from exc

    url = URL.create(
        drivername="postgresql+psycopg",
        username=user,
        password=password if password else None,
        host=host,
        port=port_number,
        database=name,
    )

    return url.render_as_string(hide_password=False)


DATABASE_URL = _build_database_url()

engine = create_engine(
    DATABASE_URL,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_session():
    """
    FastAPI request-scoped database dependency.

    A new SQLAlchemy Session is created for the request and is
    always closed when the dependency lifecycle ends.
    """

    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


def create_application_session():
    """
    Create an application-owned SQLAlchemy session.

    The caller owns the lifecycle and must eventually call
    session.close().
    """

    return SessionLocal()
