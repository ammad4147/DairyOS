import importlib


def test_local_dairyos_role_can_build_passwordless_production_url(monkeypatch):
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    monkeypatch.delenv("DAIRYOS_DATABASE_URL", raising=False)
    monkeypatch.setenv("DAIRYOS_DB_HOST", "127.0.0.1")
    monkeypatch.setenv("DAIRYOS_DB_PORT", "5432")
    monkeypatch.setenv("DAIRYOS_DB_NAME", "dairyos")
    monkeypatch.setenv("DAIRYOS_DB_USER", "dairyos")
    monkeypatch.delenv("DAIRYOS_DB_PASSWORD", raising=False)

    session = importlib.import_module("dairyos.data.database.session")
    url = session._build_database_url()

    assert url == "postgresql+psycopg://dairyos@127.0.0.1:5432/dairyos"


def test_non_local_production_still_requires_database_password(monkeypatch):
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    monkeypatch.delenv("DAIRYOS_DATABASE_URL", raising=False)
    monkeypatch.setenv("DAIRYOS_DB_HOST", "db.example.invalid")
    monkeypatch.setenv("DAIRYOS_DB_PORT", "5432")
    monkeypatch.setenv("DAIRYOS_DB_NAME", "dairyos")
    monkeypatch.setenv("DAIRYOS_DB_USER", "dairyos")
    monkeypatch.delenv("DAIRYOS_DB_PASSWORD", raising=False)

    session = importlib.import_module("dairyos.data.database.session")

    try:
        session._build_database_url()
    except RuntimeError as exc:
        assert "DAIRYOS_DB_PASSWORD" in str(exc)
    else:
        raise AssertionError(
            "non-local production database must require explicit credentials"
        )


def test_explicit_non_local_passwordless_production_url_is_rejected(monkeypatch):
    session = importlib.import_module("dairyos.data.database.session")
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    monkeypatch.setenv(
        "DAIRYOS_DATABASE_URL",
        "postgresql+psycopg://dairyos@db.example.invalid:5432/dairyos",
    )

    try:
        session._build_database_url()
    except RuntimeError as exc:
        assert "DAIRYOS_DATABASE_URL" in str(exc)
    else:
        raise AssertionError(
            "passwordless explicit remote production URL must be rejected"
        )


def test_explicit_local_passwordless_production_url_is_allowed(monkeypatch):
    session = importlib.import_module("dairyos.data.database.session")
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    monkeypatch.setenv(
        "DAIRYOS_DATABASE_URL",
        "postgresql+psycopg://dairyos@127.0.0.1:5432/dairyos",
    )

    assert session._build_database_url().endswith("/dairyos")


def test_passwordless_loopback_allows_explicit_disposable_test_database(monkeypatch):
    session = importlib.import_module("dairyos.data.database.session")
    monkeypatch.delenv("DAIRYOS_DATABASE_URL", raising=False)
    monkeypatch.delenv("DAIRYOS_DB_PASSWORD", raising=False)
    monkeypatch.setenv("DAIRYOS_DB_NAME", "dairyos_test_ai_assistant")
    monkeypatch.setenv("DAIRYOS_DB_USER", "dairyos")
    monkeypatch.setenv("DAIRYOS_DB_HOST", "127.0.0.1")
    assert "dairyos_test_ai_assistant" in session._build_database_url()


def test_passwordless_non_test_database_still_requires_production_secret(monkeypatch):
    session = importlib.import_module("dairyos.data.database.session")
    monkeypatch.delenv("DAIRYOS_DATABASE_URL", raising=False)
    monkeypatch.delenv("DAIRYOS_DB_PASSWORD", raising=False)
    monkeypatch.setenv("DAIRYOS_DB_NAME", "farm_backup")
    monkeypatch.setenv("DAIRYOS_ENV", "production")
    try:
        session._build_database_url()
    except RuntimeError as exc:
        assert "DAIRYOS_DB_PASSWORD" in str(exc)
    else:  # pragma: no cover - assertion documents the security contract
        raise AssertionError(
            "non-test production database accepted passwordless access"
        )

def _hostile_libpq_state(monkeypatch):
    hostile = {
        "PGAPPNAME": "",
        "PGCONNECT_TIMEOUT": "",
        "PGDATABASE": "ambient_database",
        "PGHOST": "ambient.invalid",
        "PGHOSTADDR": "192.0.2.10",
        "PGOPTIONS": "-c statement_timeout=1",
        "PGPORT": "1",
        "PGSERVICE": "",
        "PGSERVICEFILE": "",
        "PGSSLMODE": "disable",
        "PGSYSCONFDIR": "",
        "PGUSER": "ambient_user",
    }
    for name, value in hostile.items():
        monkeypatch.setenv(name, value)
    return hostile


def test_central_engine_registers_physical_connect_isolation_hook():
    from sqlalchemy import event

    session = importlib.import_module(
        "dairyos.data.database.session"
    )

    assert event.contains(
        session.engine,
        "do_connect",
        session._connect_with_isolated_postgres_environment,
    )


def test_central_physical_connect_preserves_arguments_and_environment(
    monkeypatch,
):
    import os

    session = importlib.import_module(
        "dairyos.data.database.session"
    )
    hostile = _hostile_libpq_state(monkeypatch)
    monkeypatch.delenv("PGPASSFILE", raising=False)

    observed = {}
    sentinel = object()

    class FakeDialect:
        def connect(self, *args, **kwargs):
            observed["args"] = args
            observed["kwargs"] = dict(kwargs)
            observed["hostile_present"] = {
                name: name in os.environ for name in hostile
            }
            observed["pgpassfile_present"] = (
                "PGPASSFILE" in os.environ
            )
            return sentinel

    cargs = ("dialect-positional",)
    cparams = {
        "host": "127.0.0.1",
        "port": 65432,
        "dbname": "dairyos_test_connection_isolation",
        "user": "dairyos",
        "context": "dialect-owned-context",
    }

    result = session._connect_with_isolated_postgres_environment(
        FakeDialect(),
        object(),
        cargs,
        cparams,
    )

    assert result is sentinel
    assert observed["args"] == cargs
    assert observed["kwargs"] == cparams
    assert not any(observed["hostile_present"].values())
    assert observed["pgpassfile_present"] is False

    assert {
        name: os.environ[name] for name in hostile
    } == hostile
    assert "PGPASSFILE" not in os.environ


def test_central_physical_connect_restores_environment_after_failure(
    monkeypatch,
):
    import os

    session = importlib.import_module(
        "dairyos.data.database.session"
    )
    hostile = _hostile_libpq_state(monkeypatch)

    class ExpectedFailure(RuntimeError):
        pass

    class FailingDialect:
        def connect(self, *args, **kwargs):
            assert all(
                name not in os.environ for name in hostile
            )
            raise ExpectedFailure("physical connect failed")

    try:
        session._connect_with_isolated_postgres_environment(
            FailingDialect(),
            object(),
            (),
            {"host": "127.0.0.1"},
        )
    except ExpectedFailure as exc:
        assert str(exc) == "physical connect failed"
    else:
        raise AssertionError("expected physical connection failure")

    assert {
        name: os.environ[name] for name in hostile
    } == hostile


def test_central_physical_connect_isolates_every_attempt(
    monkeypatch,
):
    import os

    session = importlib.import_module(
        "dairyos.data.database.session"
    )
    hostile = _hostile_libpq_state(monkeypatch)
    observed = []

    class FakeDialect:
        def connect(self, *args, **kwargs):
            observed.append(
                all(name not in os.environ for name in hostile)
            )
            return object()

    dialect = FakeDialect()

    first = session._connect_with_isolated_postgres_environment(
        dialect,
        object(),
        (),
        {"host": "127.0.0.1"},
    )

    second = session._connect_with_isolated_postgres_environment(
        dialect,
        object(),
        (),
        {"host": "127.0.0.1"},
    )

    assert first is not second
    assert observed == [True, True]

    assert {
        name: os.environ[name] for name in hostile
    } == hostile
