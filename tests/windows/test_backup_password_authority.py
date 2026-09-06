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
