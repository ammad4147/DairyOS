import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from dairyos.data.database.base import Base

# ------------------------------------------------------------------
# Database connection configuration
# ------------------------------------------------------------------
#
# This module is the single place DairyOS reads its database connection
# configuration. A local farm installation uses the dedicated ``dairyos``
# PostgreSQL role over loopback with trust authentication, so no database
# password is required for normal DairyOS startup. Other deployments may
# provide DAIRYOS_DATABASE_URL or explicit credentials.

load_dotenv()


def _build_database_url() -> str:
    explicit_url = os.getenv("DAIRYOS_DATABASE_URL")
    if explicit_url:
        return explicit_url

    environment = os.getenv("DAIRYOS_ENV", "development").strip().lower()
    host = os.getenv("DAIRYOS_DB_HOST", "localhost")
    port = os.getenv("DAIRYOS_DB_PORT", "5432")
    name = os.getenv("DAIRYOS_DB_NAME", "dairyos")
    user = os.getenv(
        "DAIRYOS_DB_USER",
        "dairyos" if environment in {"production", "staging", "preprod"} else "postgres",
    )
    password = os.getenv("DAIRYOS_DB_PASSWORD")

    local_passwordless = (
        not password
        and user == "dairyos"
        and host in {"localhost", "127.0.0.1", "::1"}
    )

    if password is None and not local_passwordless:
        if environment in {"production", "staging", "preprod"}:
            raise RuntimeError(
                "DAIRYOS_DB_PASSWORD (or DAIRYOS_DATABASE_URL) must be configured "
                "for non-local production database access."
            )
        password = "postgres"

    try:
        port_number = int(port)
    except ValueError as exc:
        raise RuntimeError(
            f"DAIRYOS_DB_PORT must be an integer, got {port!r}"
        ) from exc

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

    Application-level components that need a long-lived session
    must use SessionLocal() directly through their composition
    boundary rather than consuming this generator.
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

    This function exists so application composition does not
    misuse the FastAPI dependency generator.
    """

    return SessionLocal()
