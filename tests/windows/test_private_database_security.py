import inspect

from dairyos.windows import private_database_security as security


def test_bootstrap_never_blanket_reassigns_bootstrap_role():
    source = inspect.getsource(security._bootstrap_security)

    assert "REASSIGN OWNED" not in source
    assert "_transfer_application_ownership(connection, config.user)" in source


def test_application_ownership_transfer_is_scoped_to_user_schemas():
    source = inspect.getsource(security._transfer_application_ownership)

    assert "information_schema" in source
    assert "pg_%" in source
    assert "pg_class" in source
    assert "pg_proc" in source
    assert "pg_type" in source


def test_bootstrap_role_is_never_demoted():
    source = inspect.getsource(security._bootstrap_security)

    assert "ALTER ROLE {APP_ROLE} LOGIN NOSUPERUSER" not in source
    assert "app_role = LEGACY_APP_ROLE if config.user == APP_ROLE else APP_ROLE" in source


def test_legacy_bootstrap_uses_separate_restricted_application_role():
    assert security.LEGACY_APP_ROLE != security.APP_ROLE


def test_existing_security_reasserts_restricted_role_passwords(monkeypatch):
    class FakeConnection:
        def __init__(self):
            self.statements = []
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def execute(self, statement, *args):
            self.statements.append(str(statement))

    class FakeConfig:
        database = "dairyos"

    connection = FakeConnection()
    monkeypatch.setattr(security, "application_role", lambda config: "dairyos_app")
    monkeypatch.setattr(security, "_connect", lambda *args, **kwargs: connection)
    monkeypatch.setattr(security, "_literal", lambda connection, value: f"'LITERAL:{value}'")

    security._reassert_privileges(
        FakeConfig(),
        app_password="app-secret",
        admin_password="admin-secret",
        backup_password="backup-secret",
    )

    rendered = "\n".join(connection.statements)
    assert "ALTER ROLE dairyos_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD 'LITERAL:app-secret'" in rendered
    assert "ALTER ROLE dairyos_backup LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD 'LITERAL:backup-secret'" in rendered

def test_private_security_connect_isolates_ambient_libpq(
    monkeypatch,
):
    from pathlib import Path

    from dairyos.windows import private_postgres

    config = private_postgres.PrivatePostgreSQLConfig(
        runtime_root=Path("runtime"),
        data_root=Path("data"),
        host="127.0.0.1",
        port=55432,
        database="dairyos",
        user="dairyos_admin",
        bundled_version="18.6",
    )

    poisoned = {
        "PGSERVICE": "",
        "PGSERVICEFILE": "",
        "PGSYSCONFDIR": "",
        "PGHOST": "203.0.113.1",
        "PGPORT": "",
        "PGDATABASE": "wrong_database",
        "PGUSER": "wrong_user",
        "PGPASSWORD": "ambient-secret",
        "PGOPTIONS": "-c port=1",
        "PGSSLMODE": "require",
    }

    for name, value in poisoned.items():
        monkeypatch.setenv(name, value)

    before = {
        name: (
            name in private_postgres.os.environ,
            private_postgres.os.environ.get(name),
        )
        for name
        in private_postgres._POSTGRES_ENVIRONMENT_VARIABLES
    }

    captured = {}

    class FakeConnection:
        pass

    connection = FakeConnection()

    def fake_connect(**kwargs):
        captured["kwargs"] = kwargs
        captured["environment"] = {
            name: (
                name in private_postgres.os.environ,
                private_postgres.os.environ.get(name),
            )
            for name
            in private_postgres._POSTGRES_ENVIRONMENT_VARIABLES
        }
        return connection

    monkeypatch.setattr(
        security.psycopg,
        "connect",
        fake_connect,
    )

    result = security._connect(
        config,
        user="dairyos_admin",
        password=None,
    )

    assert result is connection

    for exists, value in captured["environment"].values():
        assert exists is False
        assert value is None

    assert captured["kwargs"]["host"] == "127.0.0.1"
    assert captured["kwargs"]["port"] == 55432
    assert captured["kwargs"]["dbname"] == "dairyos"
    assert captured["kwargs"]["user"] == "dairyos_admin"
    assert captured["kwargs"]["password"] is None
    assert captured["kwargs"]["connect_timeout"] == 10
    assert captured["kwargs"]["autocommit"] is True

    after = {
        name: (
            name in private_postgres.os.environ,
            private_postgres.os.environ.get(name),
        )
        for name
        in private_postgres._POSTGRES_ENVIRONMENT_VARIABLES
    }

    assert after == before


def test_private_security_connect_restores_environment_on_failure(
    monkeypatch,
):
    from pathlib import Path

    from dairyos.windows import private_postgres

    config = private_postgres.PrivatePostgreSQLConfig(
        runtime_root=Path("runtime"),
        data_root=Path("data"),
        host="127.0.0.1",
        port=55432,
        database="dairyos",
        user="dairyos_admin",
        bundled_version="18.6",
    )

    monkeypatch.setenv("PGSERVICE", "")
    monkeypatch.setenv("PGSERVICEFILE", "")
    monkeypatch.setenv("PGPORT", "")

    before = {
        name: (
            name in private_postgres.os.environ,
            private_postgres.os.environ.get(name),
        )
        for name
        in private_postgres._POSTGRES_ENVIRONMENT_VARIABLES
    }

    def failing_connect(**kwargs):
        for name in (
            private_postgres._POSTGRES_ENVIRONMENT_VARIABLES
        ):
            assert name not in private_postgres.os.environ

        raise RuntimeError("synthetic psycopg failure")

    monkeypatch.setattr(
        security.psycopg,
        "connect",
        failing_connect,
    )

    try:
        security._connect(
            config,
            user="dairyos_admin",
            password=None,
        )
    except RuntimeError as exc:
        assert str(exc) == "synthetic psycopg failure"
    else:
        raise AssertionError(
            "Expected synthetic psycopg failure."
        )

    after = {
        name: (
            name in private_postgres.os.environ,
            private_postgres.os.environ.get(name),
        )
        for name
        in private_postgres._POSTGRES_ENVIRONMENT_VARIABLES
    }

    assert after == before
