from __future__ import annotations

from dairyos.data.database import backup


def test_explicit_database_url_password_overrides_unrelated_environment_password(
    monkeypatch,
):
    monkeypatch.setenv("DAIRYOS_DB_PASSWORD", "application-password")

    args, env = backup._connection_args(
        "postgresql+psycopg://"
        "dairyos_backup:backup-password@127.0.0.1:55312/dairyos"
    )

    username_index = args.index("--username")

    assert args[username_index + 1] == "dairyos_backup"
    assert env["PGPASSWORD"] == "backup-password"


def test_restore_can_use_explicit_environment_password_override(monkeypatch):
    monkeypatch.setenv("DAIRYOS_DB_PASSWORD", "admin-environment-password")

    args, env = backup._connection_args(
        "postgresql+psycopg://"
        "dairyos_admin_test_runner:url-password@localhost:5432/dairyos_restore_test",
        allow_environment_password_override=True,
    )

    username_index = args.index("--username")

    assert args[username_index + 1] == "dairyos_admin_test_runner"
    assert env["PGPASSWORD"] == "admin-environment-password"

def test_restore_backup_can_disable_environment_password_override(
    monkeypatch,
    tmp_path,
):
    from types import SimpleNamespace

    captured = {}

    def fake_connection_args(
        database_url,
        *,
        allow_environment_password_override=False,
    ):
        captured["database_url"] = database_url
        captured["override"] = allow_environment_password_override
        return [], {}

    monkeypatch.setattr(backup, "_connection_args", fake_connection_args)
    monkeypatch.setattr(backup, "_tool", lambda name: name)
    monkeypatch.setattr(
        backup,
        "_run_postgresql_command",
        lambda command, env, operation: SimpleNamespace(
            returncode=0,
            stdout="",
            stderr="",
        ),
    )

    artifact = tmp_path / "restore.dump"
    artifact.write_bytes(b"not-empty")

    backup.restore_backup(
        "postgresql+psycopg://dairyos_admin:url-password@127.0.0.1:55312/dairyos",
        artifact,
        allow_environment_password_override=False,
    )

    assert captured["override"] is False


def test_restore_verification_uses_explicit_admin_url_password():
    import inspect

    from dairyos.data.database import restore_verification

    source = inspect.getsource(
        restore_verification.verify_latest_backup_restore
    )

    assert "allow_environment_password_override=False" in source
