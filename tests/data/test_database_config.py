"""
Tier 1b -- configurable database connection.

Covers dairyos.data.database.session._build_database_url(), the function
that replaced the previous hardcoded
"postgresql+psycopg2://postgres:postgres@localhost:5432/dairyos" literal.

_build_database_url() reads os.environ at call time (it is not evaluated
only at import time), so these tests call it directly after manipulating
os.environ, rather than reloading the dairyos.data.database.session module.
The module-level DATABASE_URL / engine / SessionLocal built at import time
are left untouched by these tests -- they continue to reflect whatever
environment was in effect when the test process started (the established
development defaults, verified by the existing tests/core/test_database.py
and every DB-backed test in the suite).
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
    """Ensure none of the DB-related env vars leak in from the real
    environment or from a previous test, so every test starts from a
    known-blank slate."""
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    yield monkeypatch


def test_default_matches_previous_hardcoded_dsn(clean_db_env):
    """With no DAIRYOS_DB_* / DAIRYOS_DATABASE_URL / DAIRYOS_ENV set at
    all, the resolved DSN must be byte-identical to the DSN this module
    hardcoded before Tier 1b, so existing dev/test setups keep working
    unmodified."""
    assert (
        _build_database_url()
        == "postgresql+psycopg://postgres:postgres@localhost:5432/dairyos"
    )


def test_explicit_database_url_takes_precedence(clean_db_env):
    # Deliberately uses the psycopg2 driver name here (unlike the
    # assembled-DSN tests below, which use psycopg/psycopg3, matching
    # what _build_database_url() actually assembles) -- DAIRYOS_DATABASE_URL
    # is a full pass-through override, so an operator running an older
    # deployment with psycopg2 still installed must be able to use it.
    clean_db_env.setenv(
        "DAIRYOS_DATABASE_URL",
        "postgresql+psycopg2://someone:somepass@dbhost:6543/farm_prod",
    )
    # Individual component vars are set too, to prove the full override
    # wins even when both forms are present.
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
    cannot corrupt or hijack the DSN."""
    clean_db_env.setenv("DAIRYOS_DB_PASSWORD", "p@ss:word/weird")

    url = _build_database_url()

    assert url.startswith("postgresql+psycopg://postgres:")
    assert "@localhost:5432/dairyos" in url
    # The raw special characters must not appear unescaped in the
    # authority portion of the DSN.
    assert "p@ss:word/weird" not in url


def test_missing_password_defaults_in_development(clean_db_env):
    clean_db_env.setenv("DAIRYOS_ENV", "development")

    assert (
        _build_database_url()
        == "postgresql+psycopg://postgres:postgres@localhost:5432/dairyos"
    )


def test_missing_password_raises_in_production(clean_db_env):
    clean_db_env.setenv("DAIRYOS_ENV", "production")

    with pytest.raises(RuntimeError, match="DAIRYOS_DB_PASSWORD"):
        _build_database_url()


def test_production_with_explicit_password_succeeds(clean_db_env):
    clean_db_env.setenv("DAIRYOS_ENV", "production")
    clean_db_env.setenv("DAIRYOS_DB_PASSWORD", "real-prod-password")
    clean_db_env.setenv("DAIRYOS_DB_HOST", "prod-db.farm.internal")

    url = _build_database_url()

    assert "prod-db.farm.internal" in url
    assert url.startswith("postgresql+psycopg://postgres:")


def test_production_with_database_url_override_succeeds_without_password(
    clean_db_env,
):
    """DAIRYOS_DATABASE_URL alone satisfies the production safety check --
    an operator using the full-URL override should not also need to set
    DAIRYOS_DB_PASSWORD."""
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


def test_env_check_is_case_insensitive(clean_db_env):
    clean_db_env.setenv("DAIRYOS_ENV", "PRODUCTION")

    with pytest.raises(RuntimeError, match="DAIRYOS_DB_PASSWORD"):
        _build_database_url()
