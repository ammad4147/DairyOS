from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from dairyos.windows import private_postgres as pg

POISONED = {
    "PGPORT": "",
    "PGHOST": "203.0.113.1",
    "PGDATA": r"C:\wrong-cluster",
    "PGDATABASE": "wrong_database",
    "PGOPTIONS": "-c port=1",
    "PGUSER": "wrong_user",
    "PGPASSWORD": "ambient-secret",
    "PGPASSFILE": r"C:\wrong-passfile",
    "PGSERVICE": "wrong_service",
    "PGSERVICEFILE": r"C:\wrong-service.conf",
    "PGSYSCONFDIR": r"C:\wrong-pg-sysconf",
}


def test_postgres_subprocess_environment_removes_ambient_authority(
    monkeypatch,
):
    for name, value in POISONED.items():
        monkeypatch.setenv(name, value)

    environment = pg._postgres_subprocess_environment()

    for name in POISONED:
        assert name not in environment


def test_postgres_subprocess_environment_restores_only_governed_user(
    monkeypatch,
):
    for name, value in POISONED.items():
        monkeypatch.setenv(name, value)

    environment = pg._postgres_subprocess_environment(
        user="dairyos_admin",
    )

    assert environment["PGUSER"] == "dairyos_admin"

    for name in POISONED:
        if name != "PGUSER":
            assert name not in environment


def test_run_sanitizes_default_postgres_environment(monkeypatch):
    for name, value in POISONED.items():
        monkeypatch.setenv(name, value)

    captured = {}

    def fake_run(command, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(pg.subprocess, "run", fake_run)

    pg._run(["postgres.exe", "--version"])

    environment = captured["env"]

    for name in POISONED:
        assert name not in environment


def test_start_pg_ctl_environment_rejects_ambient_pgport(
    monkeypatch,
    tmp_path,
):
    data_root = tmp_path / "postgres" / "data"
    data_root.mkdir(parents=True)

    (data_root / "PG_VERSION").write_text(
        "18\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("PGPORT", "")
    monkeypatch.setenv("PGHOST", "203.0.113.1")
    monkeypatch.setenv("PGDATA", r"C:\wrong-cluster")
    monkeypatch.setenv("PGUSER", "wrong_user")
    monkeypatch.setenv("PGOPTIONS", "-c port=1")

    monkeypatch.setattr(pg, "postgres_data_root", lambda: data_root)
    monkeypatch.setattr(
        pg,
        "runtime_root",
        lambda: tmp_path / "runtime" / "PostgreSQL",
    )
    monkeypatch.setattr(pg, "detect_installed_version", lambda: "18.6")
    monkeypatch.setattr(pg, "bundled_version", lambda: "18.6")
    monkeypatch.setattr(pg, "_binary", lambda name: Path(name))
    monkeypatch.setattr(pg, "_configured_port", lambda: 62628)
    monkeypatch.setattr(pg, "_read_state", lambda: {"user": "dairyos_admin"})
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
        "_ensure_role_and_database",
        lambda **kwargs: None,
    )

    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(pg, "_run", fake_run)

    config = pg.start(timeout=1)

    assert config.port == 62628

    start_calls = [
        item
        for item in calls
        if item[0][-1] == "start"
    ]

    assert len(start_calls) == 1

    command, kwargs = start_calls[0]
    environment = kwargs["env"]

    assert "-p 62628 -h 127.0.0.1" in command
    assert environment["PGUSER"] == "dairyos_admin"
    assert "PGPORT" not in environment
    assert "PGHOST" not in environment
    assert "PGDATA" not in environment
    assert "PGOPTIONS" not in environment

def test_isolated_postgres_environment_restores_exact_state(
    monkeypatch,
):
    monkeypatch.delenv("PGAPPNAME", raising=False)
    monkeypatch.setenv("PGSERVICE", "wrong_service")
    monkeypatch.setenv(
        "PGSERVICEFILE",
        r"C:\wrong-service.conf",
    )
    monkeypatch.setenv(
        "PGSYSCONFDIR",
        r"C:\wrong-pg-sysconf",
    )
    monkeypatch.setenv("PGPORT", "")
    monkeypatch.setenv("PGHOST", "203.0.113.1")
    monkeypatch.setenv("PGDATABASE", "wrong_database")
    monkeypatch.setenv("PGUSER", "wrong_user")
    monkeypatch.setenv("PGPASSWORD", "ambient-secret")
    monkeypatch.setenv("PGOPTIONS", "-c port=1")
    monkeypatch.setenv("PGSSLMODE", "require")

    before = {
        name: (
            name in pg.os.environ,
            pg.os.environ.get(name),
        )
        for name in pg._POSTGRES_ENVIRONMENT_VARIABLES
    }

    with pg.isolated_postgres_environment():
        for name in pg._POSTGRES_ENVIRONMENT_VARIABLES:
            assert name not in pg.os.environ

    after = {
        name: (
            name in pg.os.environ,
            pg.os.environ.get(name),
        )
        for name in pg._POSTGRES_ENVIRONMENT_VARIABLES
    }

    assert after == before


def test_isolated_postgres_environment_restores_after_failure(
    monkeypatch,
):
    monkeypatch.delenv("PGAPPNAME", raising=False)
    monkeypatch.setenv("PGSERVICE", "")
    monkeypatch.setenv("PGSERVICEFILE", "")
    monkeypatch.setenv("PGPORT", "")

    before = {
        name: (
            name in pg.os.environ,
            pg.os.environ.get(name),
        )
        for name in pg._POSTGRES_ENVIRONMENT_VARIABLES
    }

    try:
        with pg.isolated_postgres_environment():
            for name in pg._POSTGRES_ENVIRONMENT_VARIABLES:
                assert name not in pg.os.environ

            raise RuntimeError("deliberate test failure")
    except RuntimeError as exc:
        assert str(exc) == "deliberate test failure"

    after = {
        name: (
            name in pg.os.environ,
            pg.os.environ.get(name),
        )
        for name in pg._POSTGRES_ENVIRONMENT_VARIABLES
    }

    assert after == before
