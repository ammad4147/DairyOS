from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from dairyos.windows import private_postgres as pg


def test_postgres_is_ready_rejects_tcp_only_false_ready(monkeypatch):
    """An open TCP port must not be sufficient PostgreSQL readiness."""
    monkeypatch.setattr(pg, "_is_port_open", lambda host, port: True)
    monkeypatch.setattr(pg, "_binary", lambda name: Path(name))

    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=1, stdout="", stderr="")

    monkeypatch.setattr(pg, "_run", fake_run)

    assert pg._postgres_is_ready("127.0.0.1", 55432, timeout=1.0) is False
    assert calls
    assert calls[0][0] == "pg_isready.exe"


def test_postgres_is_ready_accepts_only_pg_isready_success(monkeypatch):
    monkeypatch.setattr(pg, "_binary", lambda name: Path(name))
    monkeypatch.setattr(
        pg,
        "_run",
        lambda command, **kwargs: SimpleNamespace(
            returncode=0,
            stdout="127.0.0.1:55432 - accepting connections",
            stderr="",
        ),
    )

    assert pg._postgres_is_ready("127.0.0.1", 55432, timeout=1.0) is True


def test_postgres_is_ready_fails_closed_when_probe_cannot_execute(monkeypatch):
    monkeypatch.setattr(pg, "_binary", lambda name: Path(name))

    def fail_run(command, **kwargs):
        raise pg.PrivatePostgreSQLError("probe failed")

    monkeypatch.setattr(pg, "_run", fail_run)

    assert pg._postgres_is_ready("127.0.0.1", 55432, timeout=1.0) is False


def test_wait_for_server_does_not_return_until_postgres_accepts(monkeypatch):
    outcomes = iter([False, False, True])
    probes: list[tuple[str, int]] = []

    def fake_ready(host, port, *, timeout):
        probes.append((host, port))
        return next(outcomes)

    clock = iter(
        [
            0.00,  # deadline construction
            0.00,  # loop condition 1
            0.00,  # remaining 1
            0.10,  # sleep calculation 1
            0.25,  # loop condition 2
            0.25,  # remaining 2
            0.35,  # sleep calculation 2
            0.50,  # loop condition 3
            0.50,  # remaining 3
        ]
    )

    monkeypatch.setattr(pg, "_postgres_is_ready", fake_ready)
    monkeypatch.setattr(pg.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(pg.time, "sleep", lambda seconds: None)

    pg._wait_for_server("127.0.0.1", 55432, timeout=5.0)

    assert probes == [
        ("127.0.0.1", 55432),
        ("127.0.0.1", 55432),
        ("127.0.0.1", 55432),
    ]


def test_wait_for_server_fails_closed_when_postgres_never_accepts(monkeypatch):
    monkeypatch.setattr(
        pg,
        "_postgres_is_ready",
        lambda host, port, *, timeout: False,
    )

    clock = iter(
        [
            0.00,  # deadline construction
            0.00,  # loop condition
            0.00,  # remaining
            0.75,  # sleep calculation
            1.00,  # next loop condition -> deadline reached
        ]
    )

    monkeypatch.setattr(pg.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(pg.time, "sleep", lambda seconds: None)

    with pytest.raises(
        pg.PrivatePostgreSQLError,
        match="did not become ready to accept database connections",
    ):
        pg._wait_for_server("127.0.0.1", 55432, timeout=1.0)


def test_persisted_cluster_running_uses_postgres_readiness(
    monkeypatch,
    tmp_path,
):
    data_root = tmp_path / "postgres" / "data"
    data_root.mkdir(parents=True)
    (data_root / "postmaster.pid").write_text("12345\n", encoding="utf-8")

    monkeypatch.setattr(pg, "postgres_data_root", lambda: data_root)
    monkeypatch.setattr(
        pg,
        "_read_state",
        lambda: {
            "host": "127.0.0.1",
            "port": 55432,
        },
    )

    readiness_calls = []

    def fake_ready(host, port, *, timeout):
        readiness_calls.append((host, port, timeout))
        return False

    monkeypatch.setattr(pg, "_postgres_is_ready", fake_ready)
    monkeypatch.setattr(pg, "_is_port_open", lambda host, port: True)

    assert pg.persisted_cluster_is_running() is False
    assert readiness_calls == [("127.0.0.1", 55432, 2.0)]


def test_status_uses_postgres_readiness_not_tcp(
    monkeypatch,
    tmp_path,
):
    data_root = tmp_path / "postgres" / "data"
    data_root.mkdir(parents=True)
    (data_root / "postmaster.pid").write_text("12345\n", encoding="utf-8")

    config = pg.PrivatePostgreSQLConfig(
        runtime_root=tmp_path / "runtime" / "PostgreSQL",
        data_root=data_root,
        host="127.0.0.1",
        port=55432,
        database="dairyos",
        user="dairyos",
        bundled_version="18.6",
    )

    monkeypatch.setattr(pg, "detect_installed_version", lambda: "18.6")
    monkeypatch.setattr(pg, "_is_port_open", lambda host, port: True)
    monkeypatch.setattr(
        pg,
        "_postgres_is_ready",
        lambda host, port, *, timeout: False,
    )

    result = pg.status(config)

    assert result.installed is True
    assert result.running is False
