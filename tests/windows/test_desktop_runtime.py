"""Tests for the Windows desktop runtime primitives that are platform-neutral."""

from __future__ import annotations

from pathlib import Path

import pytest

from dairyos.frontend import resolve_frontend_dist
from dairyos.windows.supervisor import (
    BackendWatchdog,
    ReportingSaveApi,
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
    monkeypatch.setattr(
        "dairyos.windows.supervisor.wait_for_ready",
        lambda url, config: None,
    )

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
    assert old_process.terminated is False
    assert watchdog.process is new_process


def test_backend_watchdog_clears_transient_restart_failure_after_recovery(monkeypatch):
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
    recovered_process = FakeProcess(alive=True)
    attempts = []
    readiness_attempts = []

    def fake_start_backend(config, job, port=None):
        attempts.append(port)
        if len(attempts) == 1:
            raise RuntimeError("simulated transient restart failure")
        return recovered_process, f"http://127.0.0.1:{port}"

    def fake_wait_for_ready(url, config):
        readiness_attempts.append(url)

    reloads = []

    monkeypatch.setattr(
        "dairyos.windows.supervisor.start_backend",
        fake_start_backend,
    )
    monkeypatch.setattr(
        "dairyos.windows.supervisor.wait_for_ready",
        fake_wait_for_ready,
    )

    watchdog = BackendWatchdog(
        old_process,
        "http://127.0.0.1:8123",
        SupervisorConfig(restart_attempts=2, restart_backoff=0.0),
        FakeJob(),
        lambda url: reloads.append(url),
    )

    watchdog.start()
    watchdog.thread.join(timeout=3)
    watchdog.stop()

    assert attempts == [8123, 8123]
    assert readiness_attempts == ["http://127.0.0.1:8123"]
    assert reloads == ["http://127.0.0.1:8123"]
    assert watchdog.process is recovered_process
    assert watchdog.failure is None

def test_reporting_save_api_exposes_supervisor_owned_desktop_session_token(monkeypatch):
    monkeypatch.setattr(
        "dairyos.windows.supervisor._SESSION_TOKEN",
        "supervisor-owned-token",
    )

    api = ReportingSaveApi()

    assert api.getDesktopSessionToken() == "supervisor-owned-token"


def test_desktop_session_token_is_stable_for_supervisor_lifetime(monkeypatch):
    monkeypatch.setattr(
        "dairyos.windows.supervisor._SESSION_TOKEN",
        None,
    )

    from dairyos.windows import supervisor

    first = supervisor._desktop_session_token()
    second = supervisor._desktop_session_token()

    assert first
    assert second == first


def test_auth_signing_secret_is_stable_for_supervisor_lifetime(monkeypatch):
    monkeypatch.delenv("DAIRYOS_AUTH_SECRET", raising=False)
    monkeypatch.setattr(
        "dairyos.windows.supervisor._AUTH_SIGNING_SECRET",
        None,
    )

    from dairyos.windows import supervisor

    first = supervisor._auth_signing_secret()
    second = supervisor._auth_signing_secret()

    assert first
    assert second == first


def test_watchdog_waits_for_readiness_before_recovery_callback(monkeypatch):
    class FakeProcess:
        def __init__(self, alive: bool):
            self.alive = alive

        def poll(self):
            return None if self.alive else 1

        def terminate(self):
            self.alive = False

        def wait(self, timeout=None):
            return 0

        def kill(self):
            self.alive = False

    class FakeJob:
        def assign(self, process):
            return None

    old_process = FakeProcess(alive=False)
    recovered_process = FakeProcess(alive=True)
    events = []

    def fake_start_backend(config, job, port=None):
        events.append(("start", port))
        return recovered_process, f"http://127.0.0.1:{port}"

    def fake_wait_for_ready(url, config):
        events.append(("ready", url))

    def recovered(url):
        events.append(("callback", url))

    monkeypatch.setattr(
        "dairyos.windows.supervisor.start_backend",
        fake_start_backend,
    )
    monkeypatch.setattr(
        "dairyos.windows.supervisor.wait_for_ready",
        fake_wait_for_ready,
    )

    watchdog = BackendWatchdog(
        old_process,
        "http://127.0.0.1:8123",
        SupervisorConfig(
            restart_attempts=1,
            restart_backoff=0.0,
        ),
        FakeJob(),
        recovered,
    )

    watchdog.start()
    watchdog.thread.join(timeout=2)
    watchdog.stop()

    assert events == [
        ("start", 8123),
        ("ready", "http://127.0.0.1:8123"),
        ("callback", "http://127.0.0.1:8123"),
    ]
    assert watchdog.failure is None

def test_reporting_save_api_persists_exact_bytes(tmp_path):
    destination = tmp_path / "report.pdf"
    save_dialog_type = object()

    class FakeWindow:
        def create_file_dialog(self, dialog_type, save_filename=None):
            assert dialog_type is save_dialog_type
            assert save_filename == "report.pdf"
            return str(destination)

    api = ReportingSaveApi(save_dialog_type)
    api.window = FakeWindow()

    result = api.save_reporting_export(
        "report.pdf",
        "PDF",
        "JVBERg==",
    )

    assert result["status"] == "SAVED"
    assert result["path"] == str(destination.resolve())
    assert result["bytes"] == 4
    assert destination.read_bytes() == b"%PDF"


def test_reporting_save_api_does_not_write_when_operator_cancels(tmp_path):
    class FakeWindow:
        def create_file_dialog(self, dialog_type, save_filename=None):
            return None

    api = ReportingSaveApi()
    api.window = FakeWindow()

    result = api.save_reporting_export(
        "report.csv",
        "CSV",
        "QUJD",
    )

    assert result == {"status": "CANCELLED"}
    assert list(tmp_path.iterdir()) == []


def test_reporting_save_api_rejects_unsupported_format():
    api = ReportingSaveApi()
    api.window = object()

    with pytest.raises(ValueError, match="Unsupported Reporting export format"):
        api.save_reporting_export(
            "report.txt",
            "TXT",
            "QUJD",
        )


def test_reporting_save_api_rejects_extension_format_mismatch():
    api = ReportingSaveApi()
    api.window = object()

    with pytest.raises(
        ValueError,
        match="filename extension does not match",
    ):
        api.save_reporting_export(
            "report.csv",
            "PDF",
            "JVBERg==",
        )


def test_reporting_save_api_rejects_malformed_base64():
    api = ReportingSaveApi()
    api.window = object()

    with pytest.raises(ValueError, match="Invalid report payload"):
        api.save_reporting_export(
            "report.pdf",
            "PDF",
            "not-valid-base64!",
        )


def test_reporting_save_api_strips_filename_path_components(tmp_path):
    destination = tmp_path / "report.csv"

    class FakeWindow:
        def create_file_dialog(self, dialog_type, save_filename=None):
            assert save_filename == "report.csv"
            return str(destination)

    api = ReportingSaveApi()
    api.window = FakeWindow()

    result = api.save_reporting_export(
        "../untrusted/report.csv",
        "CSV",
        "QUJD",
    )

    assert result["status"] == "SAVED"
    assert destination.read_bytes() == b"ABC"


def test_reporting_save_api_does_not_report_saved_when_write_fails(
    tmp_path,
    monkeypatch,
):
    destination = tmp_path / "report.xlsx"

    class FakeWindow:
        def create_file_dialog(self, dialog_type, save_filename=None):
            return str(destination)

    api = ReportingSaveApi()
    api.window = FakeWindow()

    def fail_write(self, content):
        raise OSError("simulated write failure")

    monkeypatch.setattr(Path, "write_bytes", fail_write)

    with pytest.raises(OSError, match="simulated write failure"):
        api.save_reporting_export(
            "report.xlsx",
            "XLSX",
            "UEsDBA==",
        )


def test_reporting_save_api_rejects_selected_destination_extension_mismatch(
    tmp_path,
):
    destination = tmp_path / "report.csv"

    class FakeWindow:
        def create_file_dialog(self, dialog_type, save_filename=None):
            assert save_filename == "report.pdf"
            return str(destination)

    api = ReportingSaveApi()
    api.window = FakeWindow()

    with pytest.raises(
        ValueError,
        match="Selected report filename extension does not match",
    ):
        api.save_reporting_export(
            "report.pdf",
            "PDF",
            "JVBERg==",
        )

    assert not destination.exists()
