"""
Tier 1b -- configurable database connection.

Covers dairyos.data.database.session._build_database_url(), the function
that replaced the previous hardcoded database DSN.

_build_database_url() reads os.environ at call time (it is not evaluated
only at import time), so these tests call it directly after manipulating
os.environ, rather than reloading the dairyos.data.database.session module.
The module-level DATABASE_URL / engine / SessionLocal built at import time
are left untouched by these tests.
"""

import os

import pytest

from dairyos.data.database.session import _build_database_url

ENV_KEYS = (
    "DAIRYOS_DATABASE_URL",
    "DAIRYOS_DB_HOST",
    "DAIRYOS_DB_PORT",
    "DAIRYOS_DB_NAME",
    "DAIRYOS_DB_USER",
    "DAIRYOS_DB_PASSWORD",
    "DAIRYOS_ENV",
)


@pytest.fixture
def clean_db_env(monkeypatch):
    """Ensure DB-related environment variables do not leak between tests."""
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    yield monkeypatch


def test_default_uses_local_dairyos_role(clean_db_env):
    """The local development default uses the dedicated dairyos role.

    The local PostgreSQL installation grants the dairyos role trust
    authentication for the DairyOS database, so the postgres superuser
    must not be the default application connection.
    """
    assert (
        _build_database_url()
        == "postgresql+psycopg://dairyos@localhost:5432/dairyos"
    )


def test_explicit_database_url_takes_precedence(clean_db_env):
    # DAIRYOS_DATABASE_URL is a complete pass-through override.
    clean_db_env.setenv(
        "DAIRYOS_DATABASE_URL",
        "postgresql+psycopg2://someone:somepass@dbhost:6543/farm_prod",
    )
    clean_db_env.setenv("DAIRYOS_DB_HOST", "ignored-host")
    clean_db_env.setenv("DAIRYOS_DB_PASSWORD", "ignored-password")

    assert (
        _build_database_url()
        == "postgresql+psycopg2://someone:somepass@dbhost:6543/farm_prod"
    )


def test_individual_components_are_assembled(clean_db_env):
    clean_db_env.setenv("DAIRYOS_DB_HOST", "db.internal.farm")
    clean_db_env.setenv("DAIRYOS_DB_PORT", "6432")
    clean_db_env.setenv("DAIRYOS_DB_NAME", "dairyos_farm1")
    clean_db_env.setenv("DAIRYOS_DB_USER", "farm1_svc")
    clean_db_env.setenv("DAIRYOS_DB_PASSWORD", "s3cret")

    assert _build_database_url() == (
        "postgresql+psycopg://farm1_svc:s3cret@db.internal.farm:6432"
        "/dairyos_farm1"
    )


def test_password_special_characters_are_escaped_not_injected(clean_db_env):
    """URL.create() must percent-encode special characters rather than
    interpolate them raw, so a password containing '@', ':' or '/'
    cannot corrupt or hijack the DSN.
    """
    clean_db_env.setenv("DAIRYOS_DB_PASSWORD", "p@ss:word/weird")

    url = _build_database_url()

    assert url.startswith("postgresql+psycopg://dairyos:")
    assert "@localhost:5432/dairyos" in url
    assert "p@ss:word/weird" not in url


def test_missing_password_defaults_to_local_dairyos_role(clean_db_env):
    clean_db_env.setenv("DAIRYOS_ENV", "development")

    assert (
        _build_database_url()
        == "postgresql+psycopg://dairyos@localhost:5432/dairyos"
    )


def test_passwordless_local_dairyos_connection_is_allowed_in_production(
    clean_db_env,
):
    clean_db_env.setenv("DAIRYOS_ENV", "production")
    clean_db_env.setenv("DAIRYOS_DB_USER", "dairyos")
    clean_db_env.setenv("DAIRYOS_DB_HOST", "127.0.0.1")
    clean_db_env.setenv("DAIRYOS_DB_NAME", "dairyos")

    assert (
        _build_database_url()
        == "postgresql+psycopg://dairyos@127.0.0.1:5432/dairyos"
    )


def test_missing_password_raises_in_production_for_non_local_deployment(
    clean_db_env,
):
    clean_db_env.setenv("DAIRYOS_ENV", "production")
    clean_db_env.setenv("DAIRYOS_DB_USER", "farm1_svc")
    clean_db_env.setenv("DAIRYOS_DB_HOST", "prod-db.farm.internal")

    with pytest.raises(RuntimeError, match="DAIRYOS_DB_PASSWORD"):
        _build_database_url()


def test_production_with_explicit_password_succeeds(clean_db_env):
    clean_db_env.setenv("DAIRYOS_ENV", "production")
    clean_db_env.setenv("DAIRYOS_DB_PASSWORD", "real-prod-password")
    clean_db_env.setenv("DAIRYOS_DB_HOST", "prod-db.farm.internal")
    clean_db_env.setenv("DAIRYOS_DB_USER", "farm1_svc")

    url = _build_database_url()

    assert "prod-db.farm.internal" in url
    assert url.startswith("postgresql+psycopg://farm1_svc:")


def test_production_with_database_url_override_succeeds_without_password(
    clean_db_env,
):
    """DAIRYOS_DATABASE_URL alone satisfies the production safety check."""
    clean_db_env.setenv("DAIRYOS_ENV", "production")
    clean_db_env.setenv(
        "DAIRYOS_DATABASE_URL",
        "postgresql+psycopg2://svc:pw@prod-db:5432/dairyos",
    )

    assert (
        _build_database_url()
        == "postgresql+psycopg2://svc:pw@prod-db:5432/dairyos"
    )


def test_invalid_port_raises_clear_error(clean_db_env):
    clean_db_env.setenv("DAIRYOS_DB_PORT", "not-a-number")

    with pytest.raises(RuntimeError, match="DAIRYOS_DB_PORT"):
        _build_database_url()


def test_env_check_is_case_insensitive_for_non_local_production(clean_db_env):
    clean_db_env.setenv("DAIRYOS_ENV", "PRODUCTION")
    clean_db_env.setenv("DAIRYOS_DB_USER", "farm1_svc")
    clean_db_env.setenv("DAIRYOS_DB_HOST", "prod-db.farm.internal")

    with pytest.raises(RuntimeError, match="DAIRYOS_DB_PASSWORD"):
        _build_database_url()
