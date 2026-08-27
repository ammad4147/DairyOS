from pathlib import Path
from unittest.mock import Mock

import pytest

from dairyos.windows import migrations


def test_empty_database_bootstrap_creates_schema_and_stamps_head(monkeypatch):
    connection = Mock()
    config = Mock()
    target = ("20260826_01",)

    base = Mock()
    metadata = Mock()
    base.metadata = metadata

    monkeypatch.setattr(
        "dairyos.data.database.base.Base",
        base,
        raising=False,
    )

    import dairyos.data.database.database as database_module

    monkeypatch.setattr(migrations, "MigrationContext", Mock())
    monkeypatch.setattr(migrations.command, "stamp", Mock())

    def fake_create_all(bind):
        assert bind is connection

    metadata.create_all.side_effect = fake_create_all

    class Verification:
        @staticmethod
        def configure(_connection):
            context = Mock()
            context.get_current_heads.return_value = target
            return context

    monkeypatch.setattr(migrations, "MigrationContext", Verification)

    migrations._bootstrap_empty_database(connection, config, target)

    metadata.create_all.assert_called_once_with(bind=connection)
    migrations.command.stamp.assert_called_once_with(config, "heads")


def test_non_empty_database_without_history_is_rejected():
    expected = "DairyOS database has application tables but no Alembic history"
    error = migrations.MigrationGateError(expected)
    assert expected in str(error)
