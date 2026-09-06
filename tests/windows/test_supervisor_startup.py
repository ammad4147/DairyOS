from types import SimpleNamespace

from dairyos.windows import supervisor


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
        "start_backend",
        lambda cfg, fake_job: calls.append("start-backend")
        or (process, "http://127.0.0.1:8000"),
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
    assert captured["env"]["DAIRYOS_DATABASE_URL"] == "postgresql+psycopg://dairyos:runtime@127.0.0.1/dairyos"
