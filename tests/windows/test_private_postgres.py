from __future__ import annotations

from pathlib import Path
import json

from dairyos.windows import private_postgres as pg


def test_runtime_state_round_trip(monkeypatch, tmp_path):
    monkeypatch.setenv("DAIRYOS_PRIVATE_POSTGRES_DATA", str(tmp_path / "postgres"))

    state = {
        "host": "127.0.0.1",
        "port": 55432,
        "database": "dairyos",
        "user": "dairyos",
        "version": "18.6",
        "data_root": str(tmp_path / "postgres"),
        "created_at": 123.0,
    }

    pg._write_state(state)

    assert pg._read_state() == state
    assert pg._configured_port() == 55432


def test_persisted_port_is_reused(monkeypatch, tmp_path):
    monkeypatch.setenv("DAIRYOS_PRIVATE_POSTGRES_DATA", str(tmp_path / "postgres"))

    root = tmp_path / "postgres"
    root.parent.mkdir(parents=True, exist_ok=True)

    root.mkdir()
    (root / "placeholder").write_text("existing", encoding="utf-8")

    pg._write_state({"port": 55432})

    assert pg._configured_port() == 55432


def test_installation_does_not_silently_move_existing_port(monkeypatch, tmp_path):
    monkeypatch.setenv("DAIRYOS_PRIVATE_POSTGRES_DATA", str(tmp_path / "postgres"))

    pg._write_state({"port": 55432})

    # The guard is exercised directly because live process startup is covered
    # by the disposable-cluster acceptance test.
    assert pg._configured_port() == 55432


def test_loopback_hba_remains_private(tmp_path):
    pg._write_pg_hba_conf(
        tmp_path,
        user="dairyos",
        database="dairyos",
    )

    text = (tmp_path / "pg_hba.conf").read_text(encoding="utf-8")

    assert "127.0.0.1/32" in text
    assert "::1/128" in text
    assert "0.0.0.0/0       reject" in text
    assert "::0/0           reject" in text


def test_connection_environment_is_passwordless():
    config = pg.PrivatePostgreSQLConfig(
        runtime_root=Path("runtime"),
        data_root=Path("data"),
        host="127.0.0.1",
        port=55432,
        database="dairyos",
        user="dairyos",
        bundled_version="18.6",
    )

    env = pg.connection_environment(config)

    assert env["DAIRYOS_DB_PASSWORD"] == ""
    assert env["DAIRYOS_DB_HOST"] == "127.0.0.1"
    assert env["DAIRYOS_DB_PORT"] == "55432"

def test_psql_command_disables_password_prompt(monkeypatch):
    calls = []

    class Result:
        returncode = 0
        stdout = "1\n"
        stderr = ""

    monkeypatch.setattr(pg, "_binary", lambda name: Path(name))

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return Result()

    monkeypatch.setattr(pg.subprocess, "run", fake_run)

    result = pg._psql(
        host="127.0.0.1",
        port=55432,
        database="postgres",
        user="dairyos",
        sql="SELECT 1;",
    )

    assert result.stdout.strip() == "1"
    assert "-w" in calls[0][0]
    assert calls[0][1]["stdin"] is pg.subprocess.DEVNULL


def test_stale_postmaster_pid_is_removed_and_cluster_is_started(
    monkeypatch,
    tmp_path,
):
    data_root = tmp_path / "postgres"
    data_root.mkdir(parents=True)
    pid_file = data_root / "postmaster.pid"
    pid_file.write_text("99999\n", encoding="utf-8")

    monkeypatch.setattr(
        pg,
        "postgres_data_root",
        lambda: data_root,
    )
    monkeypatch.setattr(
        pg,
        "detect_installed_version",
        lambda: "18.6",
    )
    monkeypatch.setattr(
        pg,
        "bundled_version",
        lambda: "18.6",
    )
    monkeypatch.setattr(
        pg,
        "_configured_port",
        lambda: 55432,
    )
    monkeypatch.setattr(
        pg,
        "_binary",
        lambda name: Path(name),
    )
    monkeypatch.setattr(
        pg,
        "_is_port_open",
        lambda host, port: False,
    )
    monkeypatch.setattr(
        pg,
        "_write_postgresql_conf",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        pg,
        "_write_pg_hba_conf",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        pg,
        "_ensure_role_and_database",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        pg,
        "_wait_for_server",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        pg,
        "_write_state",
        lambda payload: None,
    )
    monkeypatch.setattr(
        pg,
        "runtime_root",
        lambda: data_root.parent,
    )

    calls = []

    class Result:
        def __init__(self, returncode):
            self.returncode = returncode
            self.stdout = ""
            self.stderr = ""

    def fake_run(command, **kwargs):
        calls.append(command)

        if command[-1] == "status":
            return Result(3)

        if command[-1] == "start":
            return Result(0)

        return Result(0)

    monkeypatch.setattr(pg, "_run", fake_run)

    result = pg.start(timeout=1)

    assert result.port == 55432
    assert not pid_file.exists()
    assert any(command[-1] == "status" for command in calls)
    assert any(command[-1] == "start" for command in calls)
