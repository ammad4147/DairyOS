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

    result = appliance.prepare_database()

    assert result.mode == "system"
    assert result.host == "127.0.0.1"
    assert result.port == 5432
    assert result.database == "dairyos"
    assert result.user == "dairyos"
    assert result.private_postgres is None


def test_frozen_database_uses_private_postgres(monkeypatch):
    monkeypatch.setattr(appliance, "_is_frozen", lambda: True)

    class FakePrivate:
        host = "127.0.0.1"
        port = 55432
        database = "dairyos"
        user = "dairyos"

    monkeypatch.setattr(
        appliance,
        "start_private_postgres",
        lambda timeout: FakePrivate(),
    )

    result = appliance.prepare_database()

    assert result.mode == "private"
    assert result.host == "127.0.0.1"
    assert result.port == 55432
    assert result.database == "dairyos"
    assert result.user == "dairyos"
    assert result.private_postgres is not None


def test_apply_database_environment_removes_external_database_url(monkeypatch):
    database = appliance.ApplianceDatabase(
        mode="private",
        host="127.0.0.1",
        port=55432,
        database="dairyos",
        user="dairyos",
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
    assert appliance.os.environ["DAIRYOS_DB_PASSWORD"] == ""
    assert "DAIRYOS_DATABASE_URL" not in appliance.os.environ