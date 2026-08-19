from __future__ import annotations

import subprocess

import pytest

from scripts.database_backup import _pg_cli_target


def test_sqlalchemy_postgresql_url_is_normalized_for_libpq():
    cli_url, env = _pg_cli_target(
        "postgresql+psycopg://farm-user:p%40ss@localhost:5432/dairyos"
    )

    assert cli_url == "postgresql://farm-user@localhost:5432/dairyos"
    assert env["PGPASSWORD"] == "p@ss"


def test_postgresql_url_password_is_not_exposed_in_cli_target():
    cli_url, env = _pg_cli_target(
        "postgresql://farm-user:secret@localhost:5432/dairyos"
    )

    assert "secret" not in cli_url
    assert "secret" not in str([cli_url])
    assert env["PGPASSWORD"] == "secret"


def test_unsupported_database_driver_is_rejected():
    with pytest.raises(ValueError, match="Unsupported database URL driver"):
        _pg_cli_target("mysql+pymysql://user:pass@localhost/db")


def test_pg_cli_target_preserves_environment_without_overwriting_other_values(monkeypatch):
    monkeypatch.setenv("PGSSLMODE", "require")

    _, env = _pg_cli_target(
        "postgresql+psycopg://user:pass@localhost:5432/dairyos?sslmode=require"
    )

    assert env["PGSSLMODE"] == "require"
    assert env["PGPASSWORD"] == "pass"


def test_normalized_url_is_accepted_by_postgres_tools(monkeypatch):
    """The adapter emits a native PostgreSQL scheme for CLI consumers."""
    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="toc", stderr="")

    monkeypatch.setattr("scripts.database_backup.subprocess.run", fake_run)
    monkeypatch.setattr("scripts.database_backup._require", lambda name: name)

    # Avoid filesystem verification in this unit-level boundary test.
    monkeypatch.setattr("scripts.database_backup.verify", lambda dump: None)
    from pathlib import Path
    from scripts.database_backup import backup

    output = Path("backups/test-utility.dump")
    backup(
        "postgresql+psycopg://user:secret@localhost:5432/dairyos",
        output,
    )

    assert commands
    command = commands[0]
    assert command[-1] == "postgresql://user@localhost:5432/dairyos"
    assert "secret" not in " ".join(command)
