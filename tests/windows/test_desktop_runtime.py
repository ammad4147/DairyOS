"""Tests for the Windows desktop runtime primitives that are platform-neutral."""

from __future__ import annotations

from pathlib import Path

from dairyos.frontend import resolve_frontend_dist
from dairyos.windows.supervisor import SupervisorConfig, choose_port, probe, wait_for_ready


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
