from __future__ import annotations

import subprocess

import pytest

from scripts.database_backup import _pg_cli_target, backup


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


def test_backup_passes_native_url_without_password(monkeypatch, tmp_path):
    """The PostgreSQL utility receives a libpq URL, never a SQLAlchemy URL or password."""
    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        if command[0] == "pg_dump":
            output = tmp_path / "test-utility.dump"
            output.write_bytes(b"dump")
        return subprocess.CompletedProcess(command, 0, stdout="toc", stderr="")

    monkeypatch.setattr("scripts.database_backup.subprocess.run", fake_run)
    monkeypatch.setattr("scripts.database_backup._require", lambda name: name)
    monkeypatch.setattr("scripts.database_backup.verify", lambda dump: None)

    output = tmp_path / "test-utility.dump"
    backup(
        "postgresql+psycopg://user:secret@localhost:5432/dairyos",
        output,
    )

    assert commands
    command = commands[0]
    assert command[-1] == "postgresql://user@localhost:5432/dairyos"
    assert "secret" not in " ".join(command)
