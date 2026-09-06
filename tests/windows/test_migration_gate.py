from types import SimpleNamespace

import pytest

from dairyos.windows import migrations


class _Connection:
    def execute(self, *_args, **_kwargs):
        return self

    def scalar_one(self):
        return 0


class _BeginContext:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, tb):
        return False


class _Engine:
    def __init__(self, connection):
        self.connection = connection

    def begin(self):
        return _BeginContext(self.connection)

    def dispose(self):
        pass


def _patch_migration_environment(monkeypatch, current_heads, target_heads, application_tables):
    connection = _Connection()
    engine = _Engine(connection)
    config = SimpleNamespace(attributes={})
    script = SimpleNamespace(get_heads=lambda: target_heads)
    context = SimpleNamespace(get_current_heads=lambda: current_heads)

    monkeypatch.setattr(
        migrations,
        "_database_url",
        lambda: "postgresql+psycopg://dairyos:test@127.0.0.1:5432/dairyos",
    )
    monkeypatch.setattr(migrations, "_build_config", lambda: (config, script))
    monkeypatch.setattr(migrations, "create_engine", lambda *_args, **_kwargs: engine)
    monkeypatch.setattr(
        migrations.MigrationContext,
        "configure",
        lambda *_args, **_kwargs: context,
    )
    monkeypatch.setattr(
        migrations,
        "_public_application_table_count",
        lambda _connection: application_tables,
    )

    return config


def test_empty_database_uses_explicit_bootstrap(monkeypatch):
    target = ("20260826_01",)
    config = _patch_migration_environment(monkeypatch, (), target, 0)
    calls = []

    def bootstrap(connection, received_config, received_target):
        calls.append((connection, received_config, received_target))

    monkeypatch.setattr(migrations, "_bootstrap_empty_database", bootstrap)

    result = migrations.migrate_if_needed()

    assert result.migrated is True
    assert result.current_heads == ()
    assert result.target_heads == target
    assert len(calls) == 1
    assert calls[0][1] is config
    assert calls[0][2] == target


def test_non_empty_database_without_history_is_rejected(monkeypatch):
    _patch_migration_environment(monkeypatch, (), ("20260826_01",), 1)

    with pytest.raises(
        migrations.MigrationGateError,
        match="application tables but no Alembic history",
    ):
        migrations.migrate_if_needed()



def test_current_head_runtime_verifies_guards_without_reinstall(monkeypatch):
    target = ("20260905_04",)
    _patch_migration_environment(monkeypatch, target, target, 1)
    calls = []

    monkeypatch.delenv(migrations.MIGRATION_DATABASE_URL_ENV, raising=False)
    monkeypatch.setattr(
        migrations,
        "verify_destructive_guards",
        lambda connection: calls.append(("verify", connection)),
    )
    monkeypatch.setattr(
        migrations,
        "install_destructive_guards",
        lambda connection: calls.append(("install", connection)),
    )

    result = migrations.migrate_if_needed()

    assert result.migrated is False
    assert [kind for kind, _connection in calls] == ["verify"]


def test_current_head_privileged_gate_may_reinstall_guards(monkeypatch):
    target = ("20260905_04",)
    _patch_migration_environment(monkeypatch, target, target, 1)
    calls = []

    monkeypatch.setenv(
        migrations.MIGRATION_DATABASE_URL_ENV,
        "postgresql+psycopg://dairyos_admin:test@127.0.0.1:5432/dairyos",
    )
    monkeypatch.setattr(
        migrations,
        "verify_destructive_guards",
        lambda connection: calls.append(("verify", connection)),
    )
    monkeypatch.setattr(
        migrations,
        "install_destructive_guards",
        lambda connection: calls.append(("install", connection)),
    )
    monkeypatch.setattr(migrations, "restore_verification_due", lambda: False)

    result = migrations.migrate_if_needed()

    assert result.migrated is False
    assert [kind for kind, _connection in calls] == ["install"]
    assert migrations.MIGRATION_DATABASE_URL_ENV not in __import__("os").environ


def test_privileged_url_is_cleared_when_engine_creation_fails(monkeypatch):
    monkeypatch.setenv(
        migrations.MIGRATION_DATABASE_URL_ENV,
        "postgresql+psycopg://dairyos_admin:secret@127.0.0.1:5432/dairyos",
    )
    monkeypatch.setattr(
        migrations,
        "_database_url",
        lambda: "postgresql+psycopg://dairyos_admin:secret@127.0.0.1:5432/dairyos",
    )
    monkeypatch.setattr(
        migrations,
        "_build_config",
        lambda: (SimpleNamespace(attributes={}), SimpleNamespace(get_heads=lambda: ())),
    )
    monkeypatch.setattr(
        migrations,
        "create_engine",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("engine failed")),
    )
    monkeypatch.setattr(migrations, "restore_verification_due", lambda: False)

    with pytest.raises(
        migrations.MigrationGateError,
        match="database preflight failed",
    ):
        migrations.migrate_if_needed()

    assert migrations.MIGRATION_DATABASE_URL_ENV not in __import__("os").environ
