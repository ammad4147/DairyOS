from __future__ import annotations

import dairyos.windows.appliance_database as appliance


def test_development_database_uses_system_postgres(monkeypatch):
    monkeypatch.setattr(appliance, "_is_frozen", lambda: False)
    monkeypatch.setattr(
        appliance,
        "ensure_postgresql_running",
        lambda timeout: "postgresql-x64-18",
    )
    monkeypatch.setenv("DAIRYOS_DB_HOST", "127.0.0.1")
    monkeypatch.setenv("DAIRYOS_DB_PORT", "5432")
    monkeypatch.setenv("DAIRYOS_DB_NAME", "dairyos")
    monkeypatch.setenv("DAIRYOS_DB_USER", "dairyos")
    monkeypatch.setenv("DAIRYOS_DB_PASSWORD", "dev-secret")

    result = appliance.prepare_database()

    assert result.mode == "system"
    assert result.host == "127.0.0.1"
    assert result.port == 5432
    assert result.database == "dairyos"
    assert result.user == "dairyos"
    assert result.password == "dev-secret"
    assert result.private_postgres is None


def test_frozen_database_uses_separate_app_admin_and_backup_credentials(monkeypatch):
    monkeypatch.setattr(appliance, "_is_frozen", lambda: True)

    class FakePrivate:
        host = "127.0.0.1"
        port = 55432
        database = "dairyos"
        user = "dairyos"

    private = FakePrivate()
    calls = []
    monkeypatch.setattr(
        appliance,
        "start_private_postgres",
        lambda timeout: private,
    )
    monkeypatch.setattr(
        appliance,
        "install_steady_state_hba_before_start_if_available",
        lambda: calls.append("hba"),
    )
    monkeypatch.setattr(
        appliance,
        "ensure_private_database_security",
        lambda value: calls.append(("security", value)),
    )
    monkeypatch.setattr(appliance, "application_password", lambda value: "app-secret")
    monkeypatch.setattr(appliance, "application_role", lambda value: "dairyos")
    monkeypatch.setattr(appliance, "admin_database_url", lambda value: "postgresql+psycopg://admin")
    monkeypatch.setattr(appliance, "backup_database_url", lambda value: "postgresql+psycopg://backup")

    result = appliance.prepare_database()

    assert result.mode == "private"
    assert result.host == "127.0.0.1"
    assert result.port == 55432
    assert result.database == "dairyos"
    assert result.user == "dairyos"
    assert result.password == "app-secret"
    assert result.migration_database_url == "postgresql+psycopg://admin"
    assert result.backup_database_url == "postgresql+psycopg://backup"
    assert result.private_postgres is private
    assert calls == ["hba", ("security", private)]


def test_apply_database_environment_removes_external_url_and_stages_only_migration_url(monkeypatch):
    database = appliance.ApplianceDatabase(
        mode="private",
        host="127.0.0.1",
        port=55432,
        database="dairyos",
        user="dairyos",
        password_value="app-secret",
        migration_database_url="postgresql+psycopg://admin-secret@localhost/dairyos",
        backup_database_url="postgresql+psycopg://backup-secret@localhost/dairyos",
    )

    monkeypatch.setenv(
        "DAIRYOS_DATABASE_URL",
        "postgresql+psycopg://wrong/wrong",
    )

    appliance.apply_database_environment(database)

    assert appliance.os.environ["DAIRYOS_DB_HOST"] == "127.0.0.1"
    assert appliance.os.environ["DAIRYOS_DB_PORT"] == "55432"
    assert appliance.os.environ["DAIRYOS_DB_NAME"] == "dairyos"
    assert appliance.os.environ["DAIRYOS_DB_USER"] == "dairyos"
    assert appliance.os.environ["DAIRYOS_DB_PASSWORD"] == "app-secret"
    assert appliance.os.environ["DAIRYOS_MIGRATION_DATABASE_URL"].startswith("postgresql+psycopg://admin-secret")
    assert "DAIRYOS_BACKUP_DATABASE_URL" not in appliance.os.environ
    assert "DAIRYOS_DATABASE_URL" not in appliance.os.environ
