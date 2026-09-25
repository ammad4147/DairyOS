import os
import sys
from pathlib import Path
from types import SimpleNamespace

from dairyos.windows import supervisor


def test_desktop_window_uses_windows_work_area_without_fixed_bounds():
    source = Path(supervisor.__file__).read_text(encoding="utf-8")
    assert 'window.events.shown += window.maximize' in source
    assert 'width=1440' not in source
    assert 'height=900' not in source
    assert 'min_size=(1024, 700)' not in source


class _FakeProcess:
    def __init__(self):
        self.terminated = False

    def poll(self):
        return None if not self.terminated else 0

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.terminated = True


class _FakeJob:
    def __init__(self):
        self.created = False
        self.closed = False

    def create(self):
        self.created = True

    def close(self):
        self.closed = True


class _FakeWatchdog:
    def __init__(self, process, url, config, job, on_restart):
        self.process = process
        self.url = url
        self.failure = None
        self.stopped = False

    def start(self):
        pass

    def stop(self):
        self.stopped = True


def test_direct_backend_dispatch_marks_windowed_backend_mode(monkeypatch):
    captured = {}

    def server_main(argv):
        captured["argv"] = argv
        captured["mode"] = os.environ.get("DAIRYOS_BACKEND_MODE")
        return 17

    monkeypatch.delenv("DAIRYOS_BACKEND_MODE", raising=False)
    monkeypatch.setitem(
        sys.modules,
        "dairyos.server",
        SimpleNamespace(main=server_main),
    )

    assert supervisor.main(["--dairyos-backend", "--port", "8126"]) == 17
    assert captured == {
        "argv": ["--port", "8126"],
        "mode": "1",
    }


def test_browser_launcher_option_is_available_without_changing_desktop_default():
    parser = supervisor.build_parser()
    assert parser.parse_args(["--browser"]).browser is True
    assert parser.parse_args([]).browser is False


def test_network_access_is_explicit_and_uses_stable_private_network_listener():
    parser = supervisor.build_parser()

    desktop = supervisor.config_from_args(parser.parse_args([]))
    network = supervisor.config_from_args(
        parser.parse_args(["--network-access"])
    )

    assert (desktop.host, desktop.port, desktop.browser_mode) == (
        "127.0.0.1",
        0,
        False,
    )
    assert (network.host, network.port, network.browser_mode) == (
        "0.0.0.0",
        supervisor.LAN_WEB_PORT,
        True,
    )


def test_network_mode_browser_uses_private_ipv4_not_wildcard(monkeypatch):
    calls = []
    job = _FakeJob()
    process = _FakeProcess()
    config = supervisor.SupervisorConfig(
        host="0.0.0.0",
        port=supervisor.LAN_WEB_PORT,
        health_timeout=1,
        restart_attempts=0,
        postgres_timeout=1,
    )

    monkeypatch.setattr(
        supervisor,
        "SingleInstance",
        lambda: SimpleNamespace(acquire=lambda: True, release=lambda: None),
    )
    monkeypatch.setattr(supervisor, "JobObject", lambda: job)
    monkeypatch.setattr(supervisor, "ensure_postgresql_running", lambda timeout: "postgresql-test")
    monkeypatch.setattr(supervisor, "stage_runtime_database_url", lambda: None)
    monkeypatch.setattr(supervisor, "stage_migration_database_url", lambda: None)
    monkeypatch.setattr(supervisor, "migrate_if_needed", lambda: SimpleNamespace(
        migrated=False, current_heads=("head",), target_heads=("head",), backup_path=None
    ))
    monkeypatch.setattr(supervisor, "process_pending_system_reset", lambda: None)
    monkeypatch.setattr(supervisor, "start_backend", lambda cfg, fake_job, port=None: (
        process, f"http://127.0.0.1:{port}"
    ))
    monkeypatch.setattr(supervisor, "wait_for_ready", lambda url, cfg: calls.append(("ready", url)))
    monkeypatch.setattr(supervisor, "lan_ipv4_addresses", lambda: ["192.168.100.15"])

    class BrowserWatchdog(_FakeWatchdog):
        def start(self):
            self.thread = SimpleNamespace(is_alive=lambda: False)

    monkeypatch.setattr(supervisor, "BackendWatchdog", BrowserWatchdog)
    monkeypatch.setattr(
        supervisor.webbrowser,
        "open",
        lambda url, new: calls.append(("browser", url, new)) or True,
    )

    assert supervisor.run(config, browser=True) == 0
    assert calls == [
        ("ready", f"http://127.0.0.1:{supervisor.LAN_WEB_PORT}"),
        ("browser", f"http://192.168.100.15:{supervisor.LAN_WEB_PORT}", 2),
    ]
    assert process.terminated is True
    assert job.closed is True


def test_second_network_launch_reopens_the_running_browser(monkeypatch):
    opened = []
    config = supervisor.SupervisorConfig(
        host="0.0.0.0",
        port=supervisor.LAN_WEB_PORT,
        browser_mode=True,
    )
    monkeypatch.setattr(
        supervisor,
        "SingleInstance",
        lambda: SimpleNamespace(acquire=lambda: False, release=lambda: None),
    )
    monkeypatch.setattr(supervisor, "lan_ipv4_addresses", lambda: ["192.168.100.15"])
    monkeypatch.setattr(supervisor, "probe", lambda url: url.endswith("/health"))
    monkeypatch.setattr(
        supervisor.webbrowser,
        "open",
        lambda url, new: opened.append((url, new)) or True,
    )
    monkeypatch.setattr(
        supervisor,
        "show_startup_error",
        lambda *_args: (_ for _ in ()).throw(AssertionError("No error should be shown")),
    )

    assert supervisor.run(config, browser=True) == 0
    assert opened == [("http://192.168.100.15:8000", 2)]


def test_browser_mode_opens_local_application_and_keeps_supervisor_alive(monkeypatch):
    calls = []
    job = _FakeJob()
    process = _FakeProcess()
    config = supervisor.SupervisorConfig(
        host="127.0.0.1",
        port=8000,
        health_timeout=1,
        restart_attempts=0,
        postgres_timeout=1,
    )

    monkeypatch.setattr(
        supervisor,
        "SingleInstance",
        lambda: SimpleNamespace(acquire=lambda: True, release=lambda: None),
    )
    monkeypatch.setattr(supervisor, "JobObject", lambda: job)
    monkeypatch.setattr(supervisor, "ensure_postgresql_running", lambda timeout: "postgresql-test")
    monkeypatch.setattr(supervisor, "stage_runtime_database_url", lambda: None)
    monkeypatch.setattr(supervisor, "stage_migration_database_url", lambda: None)
    monkeypatch.setattr(supervisor, "migrate_if_needed", lambda: SimpleNamespace(
        migrated=False, current_heads=("head",), target_heads=("head",), backup_path=None
    ))
    monkeypatch.setattr(supervisor, "process_pending_system_reset", lambda: None)
    monkeypatch.setattr(supervisor, "start_backend", lambda cfg, fake_job, port=None: (
        process, f"http://127.0.0.1:{port}"
    ))
    monkeypatch.setattr(supervisor, "wait_for_ready", lambda url, cfg: calls.append(("ready", url)))

    class BrowserWatchdog(_FakeWatchdog):
        def start(self):
            calls.append("watchdog-start")
            self.thread = SimpleNamespace(is_alive=lambda: False)

    monkeypatch.setattr(supervisor, "BackendWatchdog", BrowserWatchdog)
    monkeypatch.setattr(supervisor.webbrowser, "open", lambda url, new: calls.append(("browser", url, new)) or True)

    assert supervisor.run(config, browser=True) == 0
    assert calls == [
        ("ready", "http://127.0.0.1:8000"),
        "watchdog-start",
        ("browser", "http://127.0.0.1:8000", 2),
    ]
    assert process.terminated is True
    assert job.closed is True


def test_successful_migration_continues_to_backend_startup(monkeypatch):
    calls = []
    job = _FakeJob()
    process = _FakeProcess()
    config = supervisor.SupervisorConfig(
        host="127.0.0.1",
        port=8000,
        health_timeout=1,
        health_interval=0.01,
        restart_attempts=0,
        restart_backoff=0,
        postgres_timeout=1,
    )

    monkeypatch.setattr(
        supervisor,
        "SingleInstance",
        lambda: SimpleNamespace(
            acquire=lambda: True,
            release=lambda: calls.append("instance-release"),
        ),
    )
    monkeypatch.setattr(supervisor, "JobObject", lambda: job)
    monkeypatch.setattr(
        supervisor,
        "ensure_postgresql_running",
        lambda timeout: "postgresql-x64-18",
    )
    monkeypatch.setattr(
        supervisor,
        "stage_runtime_database_url",
        lambda: calls.append("stage-runtime"),
    )
    monkeypatch.setattr(
        supervisor,
        "stage_migration_database_url",
        lambda: calls.append("stage-admin"),
    )
    monkeypatch.setattr(
        supervisor,
        "migrate_if_needed",
        lambda: calls.append("migrate") or SimpleNamespace(
            migrated=True,
            current_heads=("20260825_01",),
            target_heads=("20260826_01",),
            backup_path=None,
        ),
    )
    monkeypatch.setattr(
        supervisor,
        "process_pending_system_reset",
        lambda: None,
    )
    monkeypatch.setattr(
        supervisor,
        "start_backend",
        lambda cfg, fake_job, port=None: calls.append("start-backend")
        or (process, f"http://127.0.0.1:{port}"),
    )
    monkeypatch.setattr(
        supervisor,
        "wait_for_ready",
        lambda url, cfg: calls.append("ready"),
    )
    monkeypatch.setattr(supervisor, "BackendWatchdog", _FakeWatchdog)
    monkeypatch.setattr(
        supervisor,
        "launch_webview",
        lambda url, watchdog, on_closed: calls.append("webview"),
    )

    assert supervisor.run(config) == 0
    assert calls[:6] == [
        "stage-runtime",
        "stage-admin",
        "migrate",
        "start-backend",
        "ready",
        "webview",
    ]
    assert job.created is True
    assert job.closed is True
    assert "instance-release" in calls
    assert process.terminated is True


def test_migration_failure_does_not_start_backend(monkeypatch):
    calls = []
    job = _FakeJob()
    config = supervisor.SupervisorConfig(
        host="127.0.0.1",
        port=8000,
        health_timeout=1,
        restart_attempts=0,
        postgres_timeout=1,
    )

    monkeypatch.setattr(
        supervisor,
        "SingleInstance",
        lambda: SimpleNamespace(
            acquire=lambda: True,
            release=lambda: None,
        ),
    )
    monkeypatch.setattr(supervisor, "JobObject", lambda: job)
    monkeypatch.setattr(
        supervisor,
        "ensure_postgresql_running",
        lambda timeout: "postgresql-x64-18",
    )
    monkeypatch.setattr(
        supervisor,
        "stage_runtime_database_url",
        lambda: calls.append("stage-runtime"),
    )
    monkeypatch.setattr(
        supervisor,
        "stage_migration_database_url",
        lambda: calls.append("stage-admin"),
    )
    monkeypatch.setattr(
        supervisor,
        "migrate_if_needed",
        lambda: (_ for _ in ()).throw(
            supervisor.MigrationGateError("migration failed")
        ),
    )
    monkeypatch.setattr(
        supervisor,
        "show_startup_error",
        lambda title, message: calls.append((title, message)),
    )
    monkeypatch.setattr(
        supervisor,
        "start_backend",
        lambda *args, **kwargs: calls.append("start-backend")
        or (_FakeProcess(), "http://127.0.0.1:8000"),
    )

    assert supervisor.run(config) == 3
    assert "start-backend" not in calls
    assert job.created is True


def test_backend_child_never_receives_migration_database_url(monkeypatch, tmp_path):
    captured = {}
    process = _FakeProcess()

    class _AssigningJob:
        def assign(self, received):
            assert received is process

    def popen(command, **kwargs):
        captured["command"] = command
        captured["env"] = kwargs["env"]
        captured["log"] = kwargs["stdout"]
        return process

    monkeypatch.setenv(
        "DAIRYOS_MIGRATION_DATABASE_URL",
        "postgresql+psycopg://dairyos_admin:secret@127.0.0.1/dairyos",
    )
    monkeypatch.setenv(
        "DAIRYOS_DATABASE_URL",
        "postgresql+psycopg://dairyos:runtime@127.0.0.1/dairyos",
    )
    monkeypatch.setenv("DAIRYOS_RUNTIME_LOG_DIR", str(tmp_path))
    monkeypatch.setattr(supervisor.subprocess, "Popen", popen)
    monkeypatch.setattr(
        supervisor,
        "backend_command",
        lambda host, port: ["backend", host, str(port)],
    )

    result, url = supervisor.start_backend(
        supervisor.SupervisorConfig(host="127.0.0.1", port=8123),
        _AssigningJob(),
    )

    assert result is process
    assert url == "http://127.0.0.1:8123"
    assert "DAIRYOS_MIGRATION_DATABASE_URL" not in captured["env"]
    assert "DAIRYOS_BROWSER_MODE" not in captured["env"]
    assert captured["env"]["DAIRYOS_DATABASE_URL"] == "postgresql+psycopg://dairyos:runtime@127.0.0.1/dairyos"
    assert captured["log"].closed is True


def test_browser_backend_child_uses_human_access_mode(monkeypatch, tmp_path):
    captured = {}
    process = _FakeProcess()

    class _AssigningJob:
        def assign(self, received):
            assert received is process

    def popen(_command, **kwargs):
        captured["env"] = kwargs["env"]
        return process

    monkeypatch.setenv("DAIRYOS_RUNTIME_LOG_DIR", str(tmp_path))
    monkeypatch.setattr(supervisor.subprocess, "Popen", popen)
    monkeypatch.setattr(supervisor, "backend_command", lambda host, port: ["backend"])

    supervisor.start_backend(
        supervisor.SupervisorConfig(host="127.0.0.1", port=8123, browser_mode=True),
        _AssigningJob(),
    )

    assert captured["env"]["DAIRYOS_BROWSER_MODE"] == "1"


def test_backend_child_receives_private_auth_signing_secret(monkeypatch, tmp_path):
    captured = {}
    process = _FakeProcess()

    class _AssigningJob:
        def assign(self, received):
            assert received is process

    def popen(command, **kwargs):
        captured["env"] = kwargs["env"]
        return process

    monkeypatch.delenv("DAIRYOS_AUTH_SECRET", raising=False)
    monkeypatch.setattr(supervisor, "_AUTH_SIGNING_SECRET", None)
    monkeypatch.setenv("DAIRYOS_RUNTIME_LOG_DIR", str(tmp_path))
    monkeypatch.setattr(supervisor.subprocess, "Popen", popen)
    monkeypatch.setattr(
        supervisor,
        "backend_command",
        lambda host, port: ["backend", host, str(port)],
    )

    supervisor.start_backend(
        supervisor.SupervisorConfig(host="127.0.0.1", port=8125),
        _AssigningJob(),
    )

    secret = captured["env"]["DAIRYOS_AUTH_SECRET"]
    assert len(secret) >= 48
    assert secret != captured["env"]["DAIRYOS_DESKTOP_SESSION_TOKEN"]


def test_explicit_auth_signing_secret_remains_authoritative(monkeypatch):
    monkeypatch.setenv("DAIRYOS_AUTH_SECRET", "managed-auth-secret")
    monkeypatch.setattr(supervisor, "_AUTH_SIGNING_SECRET", None)

    assert supervisor._auth_signing_secret() == "managed-auth-secret"


def test_frozen_backend_child_receives_backend_mode(monkeypatch, tmp_path):
    captured = {}
    process = _FakeProcess()

    class _AssigningJob:
        def assign(self, received):
            assert received is process

    def popen(command, **kwargs):
        captured["env"] = kwargs["env"]
        return process

    monkeypatch.setattr(supervisor.sys, "frozen", True, raising=False)
    monkeypatch.setenv("DAIRYOS_RUNTIME_LOG_DIR", str(tmp_path))
    monkeypatch.setattr(supervisor.subprocess, "Popen", popen)

    result, url = supervisor.start_backend(
        supervisor.SupervisorConfig(host="127.0.0.1", port=8124),
        _AssigningJob(),
    )

    assert result is process
    assert url == "http://127.0.0.1:8124"
    assert captured["env"]["DAIRYOS_BACKEND_MODE"] == "1"


def test_startup_retries_reuse_one_supervisor_backend_port(monkeypatch):
    calls = []
    job = _FakeJob()
    process = _FakeProcess()

    config = supervisor.SupervisorConfig(
        host="127.0.0.1",
        port=0,
        health_timeout=1,
        health_interval=0.01,
        restart_attempts=1,
        restart_backoff=0,
        postgres_timeout=1,
    )

    monkeypatch.setattr(
        supervisor,
        "SingleInstance",
        lambda: SimpleNamespace(
            acquire=lambda: True,
            release=lambda: None,
        ),
    )
    monkeypatch.setattr(supervisor, "JobObject", lambda: job)
    monkeypatch.setattr(
        supervisor,
        "ensure_postgresql_running",
        lambda timeout: "postgresql-x64-18",
    )
    monkeypatch.setattr(
        supervisor,
        "stage_runtime_database_url",
        lambda: None,
    )
    monkeypatch.setattr(
        supervisor,
        "stage_migration_database_url",
        lambda: None,
    )
    monkeypatch.setattr(
        supervisor,
        "migrate_if_needed",
        lambda: SimpleNamespace(
            migrated=False,
            current_heads=("head",),
            target_heads=("head",),
            backup_path=None,
        ),
    )
    monkeypatch.setattr(
        supervisor,
        "process_pending_system_reset",
        lambda: None,
    )

    monkeypatch.setattr(
        supervisor,
        "choose_port",
        lambda host="127.0.0.1": 8127,
    )

    start_attempts = []

    def fake_start_backend(cfg, fake_job, port=None):
        start_attempts.append(port)
        if len(start_attempts) == 1:
            raise RuntimeError("simulated first startup failure")
        return process, f"http://127.0.0.1:{port}"

    monkeypatch.setattr(
        supervisor,
        "start_backend",
        fake_start_backend,
    )
    monkeypatch.setattr(
        supervisor,
        "wait_for_ready",
        lambda url, cfg: None,
    )
    monkeypatch.setattr(
        supervisor,
        "BackendWatchdog",
        _FakeWatchdog,
    )
    monkeypatch.setattr(
        supervisor,
        "launch_webview",
        lambda url, watchdog, on_closed: calls.append(("webview", url)),
    )

    assert supervisor.run(config) == 0

    assert start_attempts == [8127, 8127]
    assert calls == [("webview", "http://127.0.0.1:8127")]


def test_webview_runtime_failure_does_not_start_second_backend(monkeypatch):
    job = _FakeJob()
    process = _FakeProcess()

    config = supervisor.SupervisorConfig(
        host="127.0.0.1",
        port=0,
        health_timeout=1,
        health_interval=0.01,
        restart_attempts=2,
        restart_backoff=0,
        postgres_timeout=1,
    )

    monkeypatch.setattr(
        supervisor,
        "SingleInstance",
        lambda: SimpleNamespace(
            acquire=lambda: True,
            release=lambda: None,
        ),
    )
    monkeypatch.setattr(supervisor, "JobObject", lambda: job)
    monkeypatch.setattr(
        supervisor,
        "ensure_postgresql_running",
        lambda timeout: "postgresql-x64-18",
    )
    monkeypatch.setattr(
        supervisor,
        "stage_runtime_database_url",
        lambda: None,
    )
    monkeypatch.setattr(
        supervisor,
        "stage_migration_database_url",
        lambda: None,
    )
    monkeypatch.setattr(
        supervisor,
        "migrate_if_needed",
        lambda: SimpleNamespace(
            migrated=False,
            current_heads=("head",),
            target_heads=("head",),
            backup_path=None,
        ),
    )
    monkeypatch.setattr(
        supervisor,
        "process_pending_system_reset",
        lambda: None,
    )
    monkeypatch.setattr(
        supervisor,
        "choose_port",
        lambda host="127.0.0.1": 8128,
    )

    starts = []

    def fake_start_backend(cfg, fake_job, port=None):
        starts.append(port)
        return process, f"http://127.0.0.1:{port}"

    monkeypatch.setattr(
        supervisor,
        "start_backend",
        fake_start_backend,
    )
    monkeypatch.setattr(
        supervisor,
        "wait_for_ready",
        lambda url, cfg: None,
    )
    monkeypatch.setattr(
        supervisor,
        "BackendWatchdog",
        _FakeWatchdog,
    )
    monkeypatch.setattr(
        supervisor,
        "launch_webview",
        lambda url, watchdog, on_closed: (_ for _ in ()).throw(
            RuntimeError("simulated WebView runtime failure")
        ),
    )

    startup_errors = []
    monkeypatch.setattr(
        supervisor,
        "show_startup_error",
        lambda title, message: startup_errors.append((title, message)),
    )

    assert supervisor.run(config) == 1

    # A WebView/runtime failure must not create another backend lifetime.
    assert starts == [8128]
    assert len(startup_errors) == 1
    assert startup_errors[0][0] == "DairyOS desktop runtime failed"


def test_explicit_supervisor_port_remains_authoritative_across_startup(monkeypatch):
    job = _FakeJob()
    process = _FakeProcess()

    config = supervisor.SupervisorConfig(
        host="127.0.0.1",
        port=8130,
        health_timeout=1,
        health_interval=0.01,
        restart_attempts=0,
        restart_backoff=0,
        postgres_timeout=1,
    )

    monkeypatch.setattr(
        supervisor,
        "SingleInstance",
        lambda: SimpleNamespace(
            acquire=lambda: True,
            release=lambda: None,
        ),
    )
    monkeypatch.setattr(supervisor, "JobObject", lambda: job)
    monkeypatch.setattr(
        supervisor,
        "ensure_postgresql_running",
        lambda timeout: "postgresql-x64-18",
    )
    monkeypatch.setattr(supervisor, "stage_runtime_database_url", lambda: None)
    monkeypatch.setattr(supervisor, "stage_migration_database_url", lambda: None)
    monkeypatch.setattr(
        supervisor,
        "migrate_if_needed",
        lambda: SimpleNamespace(
            migrated=False,
            current_heads=("head",),
            target_heads=("head",),
            backup_path=None,
        ),
    )
    monkeypatch.setattr(
        supervisor,
        "process_pending_system_reset",
        lambda: None,
    )

    def unexpected_choose_port(host="127.0.0.1"):
        raise AssertionError("choose_port must not run for an explicit port")

    monkeypatch.setattr(
        supervisor,
        "choose_port",
        unexpected_choose_port,
    )

    starts = []

    def fake_start_backend(cfg, fake_job, port=None):
        starts.append(port)
        return process, f"http://127.0.0.1:{port}"

    monkeypatch.setattr(supervisor, "start_backend", fake_start_backend)
    monkeypatch.setattr(supervisor, "wait_for_ready", lambda url, cfg: None)
    monkeypatch.setattr(supervisor, "BackendWatchdog", _FakeWatchdog)
    monkeypatch.setattr(
        supervisor,
        "launch_webview",
        lambda url, watchdog, on_closed: None,
    )

    assert supervisor.run(config) == 0
    assert starts == [8130]
