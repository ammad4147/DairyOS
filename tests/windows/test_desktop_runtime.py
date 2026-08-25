"""Tests for the Windows desktop runtime primitives that are platform-neutral."""

from __future__ import annotations

from pathlib import Path

from dairyos.frontend import resolve_frontend_dist
from dairyos.windows.supervisor import (
    BackendWatchdog,
    SupervisorConfig,
    _url_port,
    choose_port,
    probe,
    wait_for_ready,
)


def test_frontend_dist_override_is_resolved(tmp_path, monkeypatch):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html></html>", encoding="utf-8")
    monkeypatch.setenv("DAIRYOS_FRONTEND_DIST", str(dist))

    assert resolve_frontend_dist() == Path(dist).resolve()


def test_choose_port_returns_bindable_loopback_port():
    port = choose_port()
    assert 1 <= port <= 65535


def test_probe_returns_false_for_unreachable_endpoint():
    port = choose_port()
    assert probe(f"http://127.0.0.1:{port}/health", timeout=0.05) is False


def test_wait_for_ready_times_out_when_backend_is_absent():
    port = choose_port()
    config = SupervisorConfig(health_timeout=0.05, health_interval=0.01)
    try:
        wait_for_ready(f"http://127.0.0.1:{port}", config)
    except RuntimeError as exc:
        assert "healthy" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("wait_for_ready unexpectedly reported readiness")


def test_url_port_extracts_explicit_backend_port():
    assert _url_port("http://127.0.0.1:8123") == 8123


def test_backend_watchdog_recovers_a_dead_backend(monkeypatch):
    class FakeProcess:
        def __init__(self, alive: bool):
            self.alive = alive
            self.terminated = False

        def poll(self):
            return None if self.alive else 1

        def terminate(self):
            self.terminated = True
            self.alive = False

        def wait(self, timeout=None):
            return 0

        def kill(self):
            self.alive = False

    class FakeJob:
        def assign(self, process):
            return None

    old_process = FakeProcess(alive=False)
    new_process = FakeProcess(alive=True)
    calls = []

    def fake_start_backend(config, job, port=None):
        calls.append((port, job))
        return new_process, f"http://127.0.0.1:{port}"

    monkeypatch.setattr("dairyos.windows.supervisor.start_backend", fake_start_backend)
    monkeypatch.setattr("dairyos.windows.supervisor.wait_for_ready", lambda url, config: None)

    watchdog = BackendWatchdog(
        old_process,
        "http://127.0.0.1:8123",
        SupervisorConfig(restart_attempts=1, restart_backoff=0.0),
        FakeJob(),
        lambda url: calls.append(("reloaded", url)),
    )
    watchdog.start()
    watchdog.thread.join(timeout=2)
    watchdog.stop()

    assert watchdog.failure is None
    assert calls[0][0] == 8123
    assert ("reloaded", "http://127.0.0.1:8123") in calls
    assert old_process.terminated is True
    assert watchdog.process is new_process
