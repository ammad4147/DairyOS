"""Disposable PostgreSQL experiments for DairyOS schema authority."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text
from sqlalchemy.exc import ProgrammingError

from dairyos.data.database import database  # noqa: F401 - register models
from dairyos.data.database.base import Base
from dairyos.data.database.session import engine

ROOT = Path(__file__).resolve().parents[2]


def _config(connection):
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option(
        "script_location",
        str(ROOT / "db_migrations"),
    )
    config.attributes["connection"] = connection
    return config


def _select_schema(connection, schema):
    connection.execute(
        text(f'SET LOCAL search_path TO "{schema}"')
    )


@contextmanager
def _disposable_schema(prefix):
    schema = f"{prefix}_{uuid4().hex}"
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            _select_schema(connection, schema)
            yield connection, schema
        finally:
            transaction.rollback()


def _tables(connection, schema):
    return set(inspect(connection).get_table_names(schema=schema))


def _normalize_type(column):
    return str(column["type"]).lower()


def _normalize_sql(value, schema):
    if value is None:
        return None
    normalized = " ".join(str(value).lower().split())
    return normalized.replace(f'"{schema.lower()}".', "")


def _sorted_tuple(values):
    return tuple(sorted(values or ()))


def _column_signature(column, schema):
    return (
        column["name"],
        _normalize_type(column),
        bool(column["nullable"]),
        _normalize_sql(column.get("default"), schema),
    )


def _primary_key_signature(inspector, table, schema):
    pk = inspector.get_pk_constraint(table, schema=schema)
    return _sorted_tuple(pk.get("constrained_columns"))


def _foreign_key_signature(inspector, table, schema):
    return tuple(
        sorted(
            (
                tuple(fk.get("constrained_columns") or ()),
                None
                if fk.get("referred_schema") == schema
                else fk.get("referred_schema"),
                fk.get("referred_table"),
                tuple(fk.get("referred_columns") or ()),
                fk.get("options") or {},
            )
            for fk in inspector.get_foreign_keys(table, schema=schema)
        )
    )


def _unique_signature(inspector, table, schema):
    return tuple(
        sorted(
            _sorted_tuple(unique.get("column_names"))
            for unique in inspector.get_unique_constraints(table, schema=schema)
        )
    )


def _index_signature(inspector, table, schema):
    return tuple(
        sorted(
            (
                bool(index.get("unique")),
                tuple(index.get("column_names") or ()),
                tuple(index.get("expressions") or ()),
                _normalize_sql(index.get("postgresql_where"), schema),
            )
            for index in inspector.get_indexes(table, schema=schema)
        )
    )


def _check_signature(inspector, table, schema):
    return tuple(
        sorted(
            _normalize_sql(check.get("sqltext"), schema)
            for check in inspector.get_check_constraints(table, schema=schema)
        )
    )


def _schema_signature(connection, schema):
    inspector = inspect(connection)
    signature = {}
    for table in sorted(set(Base.metadata.tables)):
        signature[table] = {
            "columns": tuple(
                _column_signature(column, schema)
                for column in inspector.get_columns(table, schema=schema)
            ),
            "primary_key": _primary_key_signature(inspector, table, schema),
            "foreign_keys": _foreign_key_signature(inspector, table, schema),
            "unique_constraints": _unique_signature(inspector, table, schema),
            "indexes": _index_signature(inspector, table, schema),
            "checks": _check_signature(inspector, table, schema),
        }
    return signature


def test_fresh_runtime_bootstrap_creates_complete_active_schema_and_head(client):
    del client
    with _disposable_schema("bootstrap_test") as (connection, schema):
        Base.metadata.create_all(bind=connection)
        command.stamp(_config(connection), "heads")

        assert _tables(connection, schema) == {
            *Base.metadata.tables,
            "alembic_version",
        }
        assert tuple(
            sorted(
                MigrationContext.configure(
                    connection,
                    opts={"version_table_schema": schema},
                ).get_current_heads()
            )
            ) == ("20260923_01",)


def test_alembic_environment_preserves_existing_application_loggers(client):
    del client
    application_logger = logging.getLogger(
        "dairyos.windows.supervisor.schema-contract"
    )
    application_logger.disabled = False

    with _disposable_schema("logging_test") as (connection, _schema):
        command.stamp(_config(connection), "heads")

    assert application_logger.disabled is False


def test_pure_alembic_from_empty_is_not_a_supported_bootstrap_path(client):
    del client
    with (
        _disposable_schema("alembic_empty_test") as (connection, _schema),
        pytest.raises(
            ProgrammingError,
            match='relation "animal" does not exist',
        ),
    ):
        command.upgrade(_config(connection), "heads")


def test_supported_create_all_baseline_upgrades_to_current_head(client):
    del client
    with _disposable_schema("upgrade_test") as (connection, schema):
        Base.metadata.create_all(bind=connection)
        config = _config(connection)
        command.stamp(config, "20260909_02")
        command.upgrade(config, "heads")

        active_tables = _tables(connection, schema) - {
            "alembic_version",
        }
        assert "ai_assistant_conversations" not in active_tables
        assert "ai_assistant_messages" not in active_tables
        assert active_tables == set(Base.metadata.tables)
        assert tuple(
            sorted(
                MigrationContext.configure(
                    connection,
                    opts={"version_table_schema": schema},
                ).get_current_heads()
            )
            ) == ("20260923_01",)


def test_supported_upgrade_preserves_active_schema_parity_with_fresh_bootstrap(
    client,
):
    del client
    with _disposable_schema("fresh_schema_parity") as (
        fresh_connection,
        fresh_schema,
    ):
        Base.metadata.create_all(bind=fresh_connection)
        command.stamp(_config(fresh_connection), "heads")
        fresh_signature = _schema_signature(fresh_connection, fresh_schema)

    with _disposable_schema("upgrade_schema_parity") as (
        upgrade_connection,
        upgrade_schema,
    ):
        Base.metadata.create_all(bind=upgrade_connection)
        config = _config(upgrade_connection)
        command.stamp(config, "20260909_02")
        command.upgrade(config, "heads")
        upgrade_signature = _schema_signature(
            upgrade_connection,
            upgrade_schema,
        )

    assert upgrade_signature == fresh_signature
