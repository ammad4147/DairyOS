from types import SimpleNamespace

from dairyos.windows import supervisor


def test_packaged_database_preflight_runs_migration_and_stops_private_database(
    monkeypatch,
):
    calls = []
    private = SimpleNamespace()
    database = SimpleNamespace(private_postgres=private)

    monkeypatch.setattr(
        supervisor,
        "prepare_database",
        lambda postgres_timeout: calls.append(("prepare", postgres_timeout))
        or database,
    )
    monkeypatch.setattr(
        supervisor,
        "apply_database_environment",
        lambda received: calls.append(("environment", received)),
    )
    monkeypatch.setattr(
        supervisor,
        "migrate_if_needed",
        lambda: calls.append(("migrate", None))
        or SimpleNamespace(
            migrated=True,
            current_heads=(),
            target_heads=("head",),
            backup_path=None,
        ),
    )
    monkeypatch.setattr(
        supervisor,
        "stop_private_postgres",
        lambda received: calls.append(("stop", received)),
    )

    result = supervisor.database_preflight(
        supervisor.SupervisorConfig(postgres_timeout=7)
    )

    assert result == 0
    assert calls == [
        ("prepare", 7),
        ("environment", database),
        ("migrate", None),
        ("stop", private),
    ]


def test_packaged_database_preflight_stops_database_after_migration_failure(
    monkeypatch,
):
    private = SimpleNamespace()
    database = SimpleNamespace(private_postgres=private)
    stopped = []

    monkeypatch.setattr(
        supervisor,
        "prepare_database",
        lambda postgres_timeout: database,
    )
    monkeypatch.setattr(
        supervisor,
        "apply_database_environment",
        lambda received: None,
    )
    monkeypatch.setattr(
        supervisor,
        "migrate_if_needed",
        lambda: (_ for _ in ()).throw(
            supervisor.MigrationGateError("simulated failure")
        ),
    )
    monkeypatch.setattr(
        supervisor,
        "stop_private_postgres",
        lambda received: stopped.append(received),
    )

    assert supervisor.database_preflight(supervisor.SupervisorConfig()) == 4
    assert stopped == [private]
