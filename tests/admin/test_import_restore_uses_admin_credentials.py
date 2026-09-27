"""Regression: the queued farm-data import must authenticate pg_restore with
the administrative URL's password, not the application role password that
the packaged supervisor exports in DAIRYOS_DB_PASSWORD."""

import inspect

from dairyos.admin import data_management
from dairyos.data.database import backup


def test_restore_ignores_application_password_in_environment(monkeypatch, tmp_path):
    dump = tmp_path / "farm.dump"
    dump.write_bytes(b"PGDMP")
    captured = {}

    class Completed:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(command, env, operation):
        captured["password"] = env.get("PGPASSWORD")
        return Completed()

    monkeypatch.setenv("DAIRYOS_DB_PASSWORD", "application-role-password")
    monkeypatch.setattr(backup, "_run_postgresql_command", fake_run)
    monkeypatch.setattr(backup, "_tool", lambda name: name)

    backup.restore_backup(
        "postgresql+psycopg://dairyos_admin:admin-password@127.0.0.1:53490/dairyos",
        dump,
    )

    assert captured["password"] == "admin-password"


def test_import_restores_never_allow_environment_password_override():
    source = inspect.getsource(data_management)
    calls = [line.strip() for line in source.splitlines() if "pg_restore_backup(" in line and "import" not in line]
    assert calls
    for call in calls:
        assert "allow_environment_password_override=False" in call, call
