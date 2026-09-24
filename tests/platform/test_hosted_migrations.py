"""Hosted migration safety, exercised only in a uniquely named test database."""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from dairyos.platform.hosted_migrations import (
    EMPTY_DATABASE_CONFIRM_ENV,
    HostedMigrationError,
    _database_url,
    migrate_hosted_database,
)


@pytest.fixture()
def empty_hosted_test_database():
    configured = os.environ["DAIRYOS_DATABASE_URL"]
    source_url = make_url(configured)
    database_name = f"dairyos_hosted_migration_test_{uuid4().hex[:12]}"
    admin_url = source_url.set(database="postgres")
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    admin_engine.dispose()

    target_url = source_url.set(database=database_name).render_as_string(
        hide_password=False
    )
    try:
        yield database_name, target_url
    finally:
        cleanup_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        with cleanup_engine.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
        cleanup_engine.dispose()


def test_empty_hosted_database_requires_exact_name_confirmation(
    empty_hosted_test_database, monkeypatch
):
    _database_name, database_url = empty_hosted_test_database
    monkeypatch.delenv(EMPTY_DATABASE_CONFIRM_ENV, raising=False)

    with pytest.raises(HostedMigrationError, match="set DAIRYOS_HOSTED_BOOTSTRAP_DATABASE"):
        migrate_hosted_database(database_url)

    engine = create_engine(database_url)
    try:
        assert inspect(engine).get_table_names(schema="public") == []
    finally:
        engine.dispose()


def test_unversioned_hosted_schema_is_refused_without_schema_changes(
    empty_hosted_test_database, monkeypatch
):
    _database_name, database_url = empty_hosted_test_database
    monkeypatch.delenv(EMPTY_DATABASE_CONFIRM_ENV, raising=False)
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE operator_owned_test (id integer)"))

        with pytest.raises(HostedMigrationError, match="no Alembic history"):
            migrate_hosted_database(database_url)

        assert inspect(engine).get_table_names(schema="public") == [
            "operator_owned_test"
        ]
    finally:
        engine.dispose()


def test_hosted_database_url_uses_supported_db_environment_settings(monkeypatch):
    monkeypatch.delenv("DAIRYOS_DATABASE_URL", raising=False)
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    monkeypatch.setenv("DAIRYOS_DB_HOST", "db")
    monkeypatch.setenv("DAIRYOS_DB_PORT", "5433")
    monkeypatch.setenv("DAIRYOS_DB_NAME", "dairyos_hosted_test")
    monkeypatch.setenv("DAIRYOS_DB_USER", "dairyos_test")
    monkeypatch.setenv("DAIRYOS_DB_PASSWORD", "disposable-test-secret")

    parsed = make_url(_database_url())

    assert parsed.host == "db"
    assert parsed.port == 5433
    assert parsed.database == "dairyos_hosted_test"
    assert parsed.username == "dairyos_test"


def test_confirmed_empty_hosted_database_bootstraps_and_verifies_heads(
    empty_hosted_test_database, monkeypatch
):
    database_name, database_url = empty_hosted_test_database
    monkeypatch.setenv(EMPTY_DATABASE_CONFIRM_ENV, database_name)

    first = migrate_hosted_database(database_url)
    second = migrate_hosted_database(database_url)

    assert first.migrated is True
    assert first.current_heads == ()
    assert first.target_heads
    assert second.migrated is False
    assert second.current_heads == first.target_heads
    assert second.target_heads == first.target_heads
