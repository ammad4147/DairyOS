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
