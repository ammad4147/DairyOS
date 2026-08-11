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
# Sprint / Gap-analysis Tier 1b
# ==============================
#
# Previously this module hardcoded
# "postgresql+psycopg2://postgres:postgres@localhost:5432/dairyos" as a
# literal string -- every deployment (including a real farm's
# production database) was forced onto that exact host, port,
# username, password and database name, with the password checked
# into source control. This module is now the single place DairyOS
# reads its database connection from, resolved (in order):
#
# ALSO FIXED while rebuilding this module: the driver in that hardcoded
# string was "postgresql+psycopg2", but pyproject.toml/requirements.txt
# declare "psycopg[binary]>=3.2" -- psycopg **3**, a different package
# that does not provide the "psycopg2" import name. A truly clean
# `pip install -e .` (only the project's own declared dependencies, no
# extra manual install) could not open a database connection at all --
# confirmed directly: create_engine("postgresql+psycopg2://...") raises
# ModuleNotFoundError: No module named 'psycopg2' in a venv built from
# nothing but this project's own dependency list. The driver below is
# now "postgresql+psycopg", SQLAlchemy 2.0's dialect name for psycopg 3,
# matching what the project actually declares and installs.
#
#   1. DAIRYOS_DATABASE_URL, a full SQLAlchemy connection string, for
#      deployments that need something this module's simpler
#      host/port/user/password/name knobs cannot express (custom SSL
#      parameters, a Unix socket path, a managed-cloud-database
#      connection string, etc.).
#   2. Otherwise, the individual DAIRYOS_DB_* environment variables
#      below, assembled into a connection string with
#      sqlalchemy.engine.URL.create() (NOT raw string interpolation,
#      so special characters in a password/host cannot corrupt or
#      inject into the DSN).
#
# A local ".env" file at the project root is loaded automatically
# (via python-dotenv, already a declared project dependency that was
# unused until now) so a developer machine or a single farm server
# can keep real credentials out of the shell profile and out of git
# without any extra wiring. load_dotenv() is a safe no-op when no
# ".env" file exists.
#
# The previous hardcoded values remain the *development* defaults, so
# an existing local/dev setup keeps working unmodified. In production
# (DAIRYOS_ENV=production) an explicit DAIRYOS_DB_PASSWORD or
# DAIRYOS_DATABASE_URL is required -- DairyOS refuses to silently run
# a farm's production database on the well-known "postgres" default
# password, mirroring the existing DAIRYOS_AUTH_SECRET production
# safety check in api/auth.py.

load_dotenv()


def _build_database_url() -> str:
    explicit_url = os.getenv("DAIRYOS_DATABASE_URL")
    if explicit_url:
        return explicit_url

    host = os.getenv("DAIRYOS_DB_HOST", "localhost")
    port = os.getenv("DAIRYOS_DB_PORT", "5432")
    name = os.getenv("DAIRYOS_DB_NAME", "dairyos")
    user = os.getenv("DAIRYOS_DB_USER", "postgres")
    password = os.getenv("DAIRYOS_DB_PASSWORD")

    if password is None:
        if os.getenv("DAIRYOS_ENV", "development").lower() == "production":
            raise RuntimeError(
                "DAIRYOS_DB_PASSWORD (or DAIRYOS_DATABASE_URL) must be "
                "configured in production -- refusing to start a "
                "production deployment on the development default "
                "database password."
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
        password=password,
        host=host,
        port=port_number,
        database=name,
    )

    # render_as_string(hide_password=False) returns the same DSN
    # create_engine() would build internally from a URL object; kept
    # as a plain string so DATABASE_URL below stays a drop-in
    # replacement for the previous hardcoded literal for any external
    # code/tooling that reads it.
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
