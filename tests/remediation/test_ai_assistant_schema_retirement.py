from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError

from dairyos.data.database import database  # noqa: F401 - register models
from dairyos.data.database.base import Base
from dairyos.data.database.session import engine


ROOT = Path(__file__).resolve().parents[2]

ASSISTANT_TABLES = {
    "ai_assistant_conversations",
    "ai_assistant_messages",
}

ASSISTANT_INDEXES = {
    "ix_ai_assistant_messages_created_at",
    "ix_ai_assistant_messages_conversation_id",
}


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
            connection.execute(
                text(f'CREATE SCHEMA "{schema}"')
            )
            _select_schema(connection, schema)
            yield connection, schema
        finally:
            transaction.rollback()


def _assistant_tables(connection, schema):
    return ASSISTANT_TABLES.intersection(
        inspect(connection).get_table_names(schema=schema)
    )


def _assistant_indexes(connection, schema):
    inspector = inspect(connection)
    tables = set(
        inspector.get_table_names(schema=schema)
    )
    names = set()

    for table in ASSISTANT_TABLES.intersection(tables):
        names.update(
            item["name"]
            for item in inspector.get_indexes(
                table,
                schema=schema,
            )
            if item.get("name")
        )

    return ASSISTANT_INDEXES.intersection(names)


def _current_heads(connection, schema):
    return tuple(
        sorted(
            MigrationContext.configure(
                connection,
                opts={"version_table_schema": schema},
            ).get_current_heads()
        )
    )


def test_historical_assistant_schema_is_created_then_physically_removed(client):
    # Keep this migration experiment isolated from the shared public schema.
    # Other DairyOS tests may legitimately retain application connections to
    # public while this test runs.
    del client

    with _disposable_schema("assistant_retirement") as (
        connection,
        schema,
    ):
        # Current ORM authority must contain no Assistant persistence.
        assert not ASSISTANT_TABLES.intersection(
            Base.metadata.tables
        )

        # Reproduce DairyOS's supported create_all baseline in this test's
        # private schema.
        Base.metadata.create_all(bind=connection)

        assert _assistant_tables(connection, schema) == set()

        config = _config(connection)

        # Begin immediately before the historical Assistant migration.
        command.stamp(config, "20260909_02")

        assert _current_heads(
            connection,
            schema,
        ) == ("20260909_02",)

        # Prove the retained historical migration still creates the exact
        # persistence objects that existed in that historical DairyOS state.
        command.upgrade(config, "20260911_01")

        assert _assistant_tables(
            connection,
            schema,
        ) == ASSISTANT_TABLES

        assert _assistant_indexes(
            connection,
            schema,
        ) == ASSISTANT_INDEXES

        assert _current_heads(
            connection,
            schema,
        ) == ("20260911_01",)

        # Continue through the real migration chain. The current DairyOS
        # schema must physically contain no Assistant persistence objects.
        command.upgrade(config, "heads")

        assert _assistant_tables(
            connection,
            schema,
        ) == set()

        assert _assistant_indexes(
            connection,
            schema,
        ) == set()

        assert _current_heads(
            connection,
            schema,
        ) == ("20260923_01",)


def test_assistant_retirement_tolerates_missing_historical_index(client):
    """Reproduce the schema state observed in a real upgraded installation."""
    del client

    with _disposable_schema("assistant_partial_retirement") as (
        connection,
        schema,
    ):
        Base.metadata.create_all(bind=connection)

        config = _config(connection)

        # Recreate the historical Assistant persistence state.
        command.stamp(config, "20260909_02")
        command.upgrade(config, "20260911_01")

        assert _assistant_tables(
            connection,
            schema,
        ) == ASSISTANT_TABLES

        assert _assistant_indexes(
            connection,
            schema,
        ) == ASSISTANT_INDEXES

        # Reproduce the real field defect: one historical Assistant index
        # had already disappeared before the retirement migration ran.
        connection.execute(
            text(
                'DROP INDEX '
                '"ix_ai_assistant_messages_created_at"'
            )
        )

        remaining_indexes = _assistant_indexes(
            connection,
            schema,
        )

        assert (
            "ix_ai_assistant_messages_created_at"
            not in remaining_indexes
        )

        # Current migration must converge this partially retired historical
        # state to the same Assistant-free schema.
        command.upgrade(config, "heads")

        assert _assistant_tables(
            connection,
            schema,
        ) == set()

        assert _assistant_indexes(
            connection,
            schema,
        ) == set()

        assert _current_heads(
            connection,
            schema,
        ) == ("20260923_01",)
def test_assistant_retirement_tolerates_all_historical_indexes_missing(client):
    """Retirement must not require either historical Assistant index."""
    del client

    with _disposable_schema("assistant_missing_indexes") as (
        connection,
        schema,
    ):
        Base.metadata.create_all(bind=connection)

        config = _config(connection)

        command.stamp(config, "20260909_02")
        command.upgrade(config, "20260911_01")

        assert _assistant_tables(
            connection,
            schema,
        ) == ASSISTANT_TABLES

        assert _assistant_indexes(
            connection,
            schema,
        ) == ASSISTANT_INDEXES

        for index_name in ASSISTANT_INDEXES:
            connection.execute(
                text(f'DROP INDEX "{index_name}"')
            )

        assert _assistant_indexes(
            connection,
            schema,
        ) == set()

        command.upgrade(config, "heads")

        assert _assistant_tables(
            connection,
            schema,
        ) == set()

        assert _assistant_indexes(
            connection,
            schema,
        ) == set()

        assert _current_heads(
            connection,
            schema,
        ) == ("20260923_01",)


def test_assistant_retirement_tolerates_assistant_tables_already_absent(client):
    """Retirement must be idempotent when Assistant tables are already gone."""
    del client

    with _disposable_schema("assistant_tables_absent") as (
        connection,
        schema,
    ):
        Base.metadata.create_all(bind=connection)

        config = _config(connection)

        command.stamp(config, "20260909_02")
        command.upgrade(config, "20260911_01")

        assert _assistant_tables(
            connection,
            schema,
        ) == ASSISTANT_TABLES

        connection.execute(
            text("DROP TABLE ai_assistant_messages")
        )
        connection.execute(
            text("DROP TABLE ai_assistant_conversations")
        )

        assert _assistant_tables(
            connection,
            schema,
        ) == set()

        assert _assistant_indexes(
            connection,
            schema,
        ) == set()

        command.upgrade(config, "heads")

        assert _assistant_tables(
            connection,
            schema,
        ) == set()

        assert _assistant_indexes(
            connection,
            schema,
        ) == set()

        assert _current_heads(
            connection,
            schema,
        ) == ("20260923_01",)


def test_assistant_retirement_blocks_unexpected_external_dependency(client):
    """Unexpected dependencies must block retirement instead of being deleted."""
    del client

    with _disposable_schema("assistant_dependency_guard") as (
        connection,
        schema,
    ):
        Base.metadata.create_all(bind=connection)

        config = _config(connection)

        command.stamp(config, "20260909_02")
        command.upgrade(config, "20260911_01")

        assert _assistant_tables(
            connection,
            schema,
        ) == ASSISTANT_TABLES

        # This view represents an unexpected external database object that
        # depends on historical Assistant persistence. A CASCADE retirement
        # would silently delete it. RESTRICT semantics must instead stop.
        connection.execute(
            text(
                "CREATE VIEW assistant_dependency_guard AS "
                "SELECT * FROM ai_assistant_conversations"
            )
        )

        # Use a savepoint because PostgreSQL marks the current transaction
        # failed after the expected dependency error.
        savepoint = connection.begin_nested()

        try:
            command.upgrade(config, "heads")
        except DBAPIError:
            savepoint.rollback()
        else:
            savepoint.rollback()
            raise AssertionError(
                "Assistant retirement unexpectedly removed an external "
                "dependency instead of blocking"
            )

        inspector = inspect(connection)

        assert (
            "assistant_dependency_guard"
            in inspector.get_view_names(schema=schema)
        )

        assert _assistant_tables(
            connection,
            schema,
        ) == ASSISTANT_TABLES

        # Migration version must not falsely advance after the blocked
        # retirement attempt.
        assert _current_heads(
            connection,
            schema,
        ) != ("20260923_01",)